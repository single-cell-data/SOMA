import contextlib
import enum
from concurrent import futures
from typing import Any, Dict, Optional, Sequence, Tuple, Union

import anndata
import attrs
import numpy as np
import numpy.typing as npt
import pandas as pd
import pyarrow as pa
from scipy import sparse
from typing_extensions import Literal, TypedDict, assert_never

from somacore import composed
from somacore import data
from somacore.query import axis


class AxisColumnNames(TypedDict, total=False):
    """Specifies column names for experiment axis query read operations."""

    obs: Optional[Sequence[str]]
    """obs columns to use. All columns if ``None`` or not present."""
    var: Optional[Sequence[str]]
    """var columns to use. All columns if ``None`` or not present."""


class ExperimentAxisQuery(contextlib.AbstractContextManager):
    """Axis-based query against a SOMA Experiment.

    ExperimentAxisQuery allows easy selection and extraction of data from a
    single soma.Measurement in a soma.Experiment, by obs/var (axis) coordinates
    and/or value filter [lifecycle: experimental].

    The primary use for this class is slicing Experiment ``X`` layers by obs or
    var value and/or coordinates. Slicing on SparseNDArray ``X`` matrices is
    supported; DenseNDArray is not supported at this time.

    IMPORTANT: this class is not thread-safe.

    IMPORTANT: this query class assumes it can store the full result of both
    axis dataframe queries in memory, and only provides incremental access to
    the underlying X NDArray. API features such as `n_obs` and `n_vars` codify
    this in the API.

    IMPORTANT: you must call `close()` on any instance of this class in order to
    release underlying resources. The ExperimentAxisQuery is a context manager,
    and it is recommended that you use the following pattern to make this easy
    and safe::

        with ExperimentAxisQuery(...) as query:
            ...

    This base query implementation is designed to work against any SOMA
    implementation that fulfills the basic APIs. A SOMA implementation may
    include a custom query implementation optimized for its own use.
    """

    def __init__(
        self,
        experiment: "composed.Experiment",
        measurement_name: str,
        *,
        obs_query: axis.AxisQuery = axis.AxisQuery(),
        var_query: axis.AxisQuery = axis.AxisQuery(),
    ):
        if measurement_name not in experiment.ms:
            raise ValueError("Measurement does not exist in the experiment")

        self.experiment = experiment
        self.measurement_name = measurement_name

        self._matrix_axis_query = _MatrixAxisQuery(obs=obs_query, var=var_query)
        self._joinids = _JoinIDCache(self)
        self._indexer = _AxisIndexer(self)
        self._threadpool_: Optional[futures.ThreadPoolExecutor] = None

    def obs(
        self, *, column_names: Optional[Sequence[str]] = None
    ) -> data.ReadIter[pa.Table]:
        """Returns ``obs`` as an Arrow table iterator."""
        obs_query = self._matrix_axis_query.obs
        return self._obs_df.read(
            ids=obs_query.coords,
            value_filter=obs_query.value_filter,
            column_names=column_names,
        )

    def var(
        self, *, column_names: Optional[Sequence[str]] = None
    ) -> data.ReadIter[pa.Table]:
        """Returns ``var`` as an Arrow table iterator."""
        var_query = self._matrix_axis_query.var
        return self._var_df.read(
            ids=var_query.coords,
            value_filter=var_query.value_filter,
            column_names=column_names,
        )

    def obs_joinids(self) -> pa.Array:
        """Returns ``obs`` ``soma_joinids`` as an Arrow array."""
        return self._joinids.obs

    def var_joinids(self) -> pa.Array:
        """Returns ``var`` ``soma_joinids`` as an Arrow array."""
        return self._joinids.var

    @property
    def n_obs(self) -> int:
        """The number of ``obs`` axis query results."""
        return len(self.obs_joinids())

    @property
    def n_vars(self) -> int:
        """The number of ``var`` axis query results."""
        return len(self.var_joinids())

    def X(self, layer_name: str) -> data.SparseRead:
        """Returns an ``X`` layer as ``SparseRead`` data.

        :param layer_name: The X layer name to return.
        """
        try:
            x_layer = self._ms.X[layer_name]
        except KeyError as ke:
            raise KeyError(f"{layer_name} is not present in X") from ke
        if not isinstance(x_layer, data.SparseNDArray):
            raise TypeError("X layers may only be sparse arrays")

        self._joinids.preload(self._threadpool)
        return x_layer.read((self._joinids.obs, self._joinids.var))

    def obsp(self, layer: str) -> data.SparseRead:
        """Return an ``obsp`` layer as a SparseNDArrayRead"""
        return self._axisp_inner(_Axis.OBS, layer)

    def varp(self, layer: str) -> data.SparseRead:
        """Return an ``varp`` layer as a SparseNDArrayRead"""
        return self._axisp_inner(_Axis.VAR, layer)

    def to_anndata(
        self,
        X_name: str,
        *,
        column_names: Optional[AxisColumnNames] = None,
        X_layers: Sequence[str] = (),
    ) -> anndata.AnnData:
        """
        Execute the query and return result as an ``AnnData`` in-memory object.

        :param X_name: The name of the X layer to read and return
            in the ``X`` slot.
        :param column_names: The columns in the ``var`` and ``obs`` dataframes
            to read.
        :param X_layers: Additional X layers to read and return
            in the ``layers`` slot.
        """
        query_result = self._read(
            X_name,
            column_names=column_names or AxisColumnNames(obs=None, var=None),
            X_layers=X_layers,
        )

        # AnnData uses positional indexing
        return self._indexer.rewrite(query_result).to_anndata()

    # Context management

    def close(self) -> None:
        """Releases resources associated with this query.

        This method must be idempotent.
        """
        if self._threadpool_:
            self._threadpool_.shutdown()
            self._threadpool_ = None

    def __exit__(self, *_: Any) -> None:
        self.close()

    def __del__(self) -> None:
        """Ensure that we're closed when our last ref disappears."""
        # If any superclass in our MRO has a __del__, call it.
        sdel = getattr(super(), "__del__", lambda: None)
        sdel()
        self.close()

    # Internals

    def _read(
        self,
        X_name: str,
        *,
        column_names: AxisColumnNames,
        X_layers: Sequence[str],
    ) -> "_AxisQueryResult":
        """Reads the entire query result into in-memory Arrow tables.

        This is a low-level routine intended to be used by loaders for other
        in-core formats, such as AnnData, which can be created from the
        resulting Tables.

        :param X_name: The name of the X layer to read and return
            in the ``AnnData.X`` slot
        :param column_names: Specify which column names in ``var`` and ``obs``
            dataframes to read and return.
        :param X_layers: Addtional X layers read read and return in the
            ``AnnData.layers`` slot

        """
        x_collection = self._ms.X
        all_x_names = [X_name] + list(X_layers)
        all_x_arrays: Dict[str, data.SparseNDArray] = {}
        for _xname in all_x_names:
            if not isinstance(_xname, str) or not _xname:
                raise ValueError("X layer names must be specified as a string.")
            if _xname not in x_collection:
                raise ValueError("Unknown X layer name")
            x_array = x_collection[_xname]
            if not isinstance(x_array, data.SparseNDArray):
                raise NotImplementedError("Dense array unsupported")
            all_x_arrays[_xname] = x_array

        obs_table, var_table = self._read_both_axes(column_names)

        x_tables = {
            # TODO: could also be done concurrently
            _xname: all_x_arrays[_xname]
            .read((self.obs_joinids(), self.var_joinids()))
            .tables()
            .concat()
            for _xname in all_x_arrays
        }

        x = x_tables.pop(X_name)
        return _AxisQueryResult(obs=obs_table, var=var_table, X=x, X_layers=x_tables)

    def _read_both_axes(
        self,
        column_names: AxisColumnNames,
    ) -> Tuple[pa.Table, pa.Table]:
        """Reads both axes in their entirety, ensuring soma_joinid is retained."""
        obs_ft = self._threadpool.submit(
            self._read_axis_dataframe,
            _Axis.OBS,
            column_names,
        )
        var_ft = self._threadpool.submit(
            self._read_axis_dataframe,
            _Axis.VAR,
            column_names,
        )
        return obs_ft.result(), var_ft.result()

    def _read_axis_dataframe(
        self,
        axis: "_Axis",
        axis_column_names: AxisColumnNames,
    ) -> pa.Table:
        """Reads the specified axis. Will cache join IDs if not present."""
        # mypy is not currently clever enough to figure out the type of the
        # column names here, so we have to help it out.
        column_names: Optional[Sequence[str]] = axis_column_names.get(axis.value)
        if axis is _Axis.OBS:
            axis_df = self._obs_df
            axis_query = self._matrix_axis_query.obs
        elif axis is _Axis.VAR:
            axis_df = self._var_df
            axis_query = self._matrix_axis_query.var
        else:
            assert_never(axis)  # must be obs or var

        # If we can cache join IDs, prepare to add them to the cache.
        joinids_cached = self._joinids._is_cached(axis)
        query_columns = column_names
        if (
            not joinids_cached
            and column_names is not None
            and "soma_joinid" not in column_names
        ):
            # If we want to fill the join ID cache, ensure that we query the
            # soma_joinid column so that it is included in the results.
            # We'll filter it out later.
            query_columns = ["soma_joinid"] + list(column_names)

        # Do the actual query.
        arrow_table = axis_df.read(
            ids=axis_query.coords,
            value_filter=axis_query.value_filter,
            column_names=query_columns,
        ).concat()

        # Update the cache if needed. We can do this because no matter what
        # other columns are queried for, the contents of the `soma_joinid`
        # column will be the same and can be safely stored.
        if not joinids_cached:
            setattr(
                self._joinids,
                axis.value,
                arrow_table.column("soma_joinid").combine_chunks(),
            )

        # Ensure that we return the exact columns the caller was expecting,
        # even if we added our own above.
        if column_names is not None:
            arrow_table = arrow_table.select(column_names)
        return arrow_table

    def _axisp_inner(
        self,
        axis: "_Axis",
        layer: str,
    ) -> data.SparseRead:
        key = axis.value + "p"

        if key not in self._ms:
            raise ValueError(f"Measurement does not contain {key} data")

        axisp = self._ms.obsp if axis is _Axis.OBS else self._ms.varp
        if not (layer and layer in axisp):
            raise ValueError(f"Must specify '{key}' layer")
        if not isinstance(axisp[layer], data.SparseNDArray):
            raise TypeError(f"Unexpected SOMA type stored in '{key}' layer")

        joinids = getattr(self._joinids, axis.value)
        return axisp[layer].read((joinids, joinids))

    @property
    def _obs_df(self) -> data.DataFrame:
        return self.experiment.obs

    @property
    def _ms(self) -> composed.Measurement:
        return self.experiment.ms[self.measurement_name]

    @property
    def _var_df(self) -> data.DataFrame:
        return self._ms.var

    @property
    def _threadpool(self) -> futures.ThreadPoolExecutor:
        """Creates a thread pool just in time."""
        if self._threadpool_ is None:
            # TODO: the user should be able to set their own threadpool, a la asyncio's
            # loop.set_default_executor().  This is important for managing the level of
            # concurrency, etc.
            self._threadpool_ = futures.ThreadPoolExecutor()
        return self._threadpool_


# Private internal data structures


@attrs.define(frozen=True)
class _AxisQueryResult:
    """Return type for the ExperimentAxisQuery.read() method"""

    obs: pa.Table
    """Experiment.obs query slice, as an Arrow Table"""
    var: pa.Table
    """Experiment.ms[...].var query slice, as an Arrow Table"""
    X: pa.Table
    """Experiment.ms[...].X[...] query slice, as an Arrow Table"""
    X_layers: Dict[str, pa.Table] = attrs.field(factory=dict)
    """Any additional X layers requested, as Arrow Table(s)"""

    def to_anndata(self) -> anndata.AnnData:
        """Convert to AnnData"""
        obs = self.obs.to_pandas()
        obs.index = obs.index.map(str)

        var = self.var.to_pandas()
        var.index = var.index.map(str)

        shape = (len(obs), len(var))

        x = self.X
        if x is not None:
            x = _arrow_to_scipy_csr(x, shape)

        layers = {
            name: _arrow_to_scipy_csr(table, shape)
            for name, table in self.X_layers.items()
        }
        return anndata.AnnData(X=x, obs=obs, var=var, layers=(layers or None))


class _Axis(enum.Enum):
    OBS = "obs"
    VAR = "var"

    @property
    def value(self) -> Literal["obs", "var"]:
        return super().value


@attrs.define(frozen=True)
class _MatrixAxisQuery:
    """Private: store per-axis user query definition"""

    obs: axis.AxisQuery
    var: axis.AxisQuery


@attrs.define
class _JoinIDCache:
    """Private: cache per-axis join ids in the query"""

    owner: ExperimentAxisQuery

    _cached_obs: Optional[pa.Array] = None
    _cached_var: Optional[pa.Array] = None

    def _is_cached(self, axis: _Axis) -> bool:
        field = "_cached_" + axis.value
        return getattr(self, field) is not None

    def preload(self, pool: futures.ThreadPoolExecutor) -> None:
        if self._cached_obs is not None and self._cached_var is not None:
            return
        obs_ft = pool.submit(lambda: self.obs)
        var_ft = pool.submit(lambda: self.var)
        # Wait for them and raise in case of error.
        obs_ft.result()
        var_ft.result()

    @property
    def obs(self) -> pa.Array:
        """Join IDs for the obs axis. Will load and cache if not already."""
        if not self._cached_obs:
            self._cached_obs = _load_joinids(
                self.owner._obs_df, self.owner._matrix_axis_query.obs
            )
        return self._cached_obs

    @obs.setter
    def obs(self, val: pa.Array) -> None:
        self._cached_obs = val

    @property
    def var(self) -> pa.Array:
        """Join IDs for the var axis. Will load and cache if not already."""
        if not self._cached_var:
            self._cached_var = _load_joinids(
                self.owner._var_df, self.owner._matrix_axis_query.var
            )
        return self._cached_var

    @var.setter
    def var(self, val: pa.Array) -> None:
        self._cached_var = val


def _load_joinids(df: data.DataFrame, axq: axis.AxisQuery) -> pa.Array:
    tbl = df.read(
        ids=axq.coords,
        value_filter=axq.value_filter,
        column_names=["soma_joinid"],
    ).concat()
    return tbl.column("soma_joinid").combine_chunks()


_Numpyable = Union[pa.Array, pa.ChunkedArray, npt.NDArray[np.int64]]
"""Things that can be converted to a NumPy array."""


@attrs.define
class _AxisIndexer:
    """Given a query, providing index-bulding services for obs/var axis."""

    query: ExperimentAxisQuery
    _cached_obs: Optional[pd.Index] = None
    _cached_var: Optional[pd.Index] = None

    @property
    def _obs_index(self) -> pd.Index:
        if self._cached_obs is None:
            self._cached_obs = pd.Index(data=self.query.obs_joinids().to_numpy())
        return self._cached_obs

    @property
    def _var_index(self) -> pd.Index:
        if self._cached_var is None:
            self._cached_var = pd.Index(data=self.query.var_joinids().to_numpy())
        return self._cached_var

    def by_obs(self, coords: _Numpyable) -> npt.NDArray[np.intp]:
        return self._obs_index.get_indexer(_to_numpy(coords))

    def by_var(self, coords: _Numpyable) -> npt.NDArray[np.intp]:
        return self._var_index.get_indexer(_to_numpy(coords))

    def rewrite(self, qr: _AxisQueryResult) -> _AxisQueryResult:
        """Rewrite the result to prepare for AnnData positional indexing."""
        return attrs.evolve(
            qr,
            X=self._rewrite_matrix(qr.X),
            X_layers={
                name: self._rewrite_matrix(matrix)
                for name, matrix in qr.X_layers.items()
            },
        )

    def _rewrite_matrix(self, x_table: pa.Table) -> pa.Table:
        """
        Private convenience function to convert axis dataframe to X matrix joins
        from ``soma_joinid``-based joins to positionally indexed joins
        (like AnnData uses).

        Input is organized as:
            obs[i] annotates X[ obs[i].soma_joinid, : ]
        and
            var[j] annotates X[ :, var[j].soma_joinid ]

        Output is organized as:
            obs[i] annotates X[i, :]
        and
            var[j] annotates X[:, j]

        In addition, the ``soma_joinid`` column is dropped from axis dataframes.
        """

        return pa.Table.from_arrays(
            (
                self.by_obs(x_table["soma_dim_0"]),
                self.by_var(x_table["soma_dim_1"]),
                # This consolidates chunks as a side effect.
                x_table["soma_data"].to_numpy(),
            ),
            names=("_dim_0", "_dim_1", "soma_data"),
        )


def _to_numpy(it: _Numpyable) -> np.ndarray:
    if isinstance(it, np.ndarray):
        return it
    return it.to_numpy()


def _arrow_to_scipy_csr(
    arrow_table: pa.Table, shape: Tuple[int, int]
) -> sparse.csr_matrix:
    """
    Private utility which converts a table repesentation of X to a CSR matrix.

    IMPORTANT: by convention, assumes that the data is positionally indexed (hence
    the use of _dim_{n} rather than soma_dim{n}).

    See query.py::_rewrite_X_for_positional_indexing for more info.
    """
    assert "_dim_0" in arrow_table.column_names, "X must be positionally indexed"
    assert "_dim_1" in arrow_table.column_names, "X must be positionally indexed"

    return sparse.csr_matrix(
        (
            arrow_table["soma_data"].to_numpy(),
            (arrow_table["_dim_0"].to_numpy(), arrow_table["_dim_1"].to_numpy()),
        ),
        shape=shape,
    )
