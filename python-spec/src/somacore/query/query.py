import enum
from concurrent import futures
from typing import (
    Any,
    Dict,
    Generic,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    overload,
)

import anndata
import attrs
import numpy as np
import numpy.typing as npt
import pandas as pd
import pyarrow as pa
from scipy import sparse
from typing_extensions import Literal, Protocol, Self, TypedDict

from .. import data
from .. import measurement
from .. import options
from . import _fast_csr
from . import axis

_RO_AUTO = options.ResultOrder.AUTO


class AxisColumnNames(TypedDict, total=False):
    """
    Specifies column names for experiment axis query read operations.

    Lifecycle: maturing
    """

    obs: Optional[Sequence[str]]
    """obs columns to use. All columns if ``None`` or not present."""
    var: Optional[Sequence[str]]
    """var columns to use. All columns if ``None`` or not present."""


_Exp = TypeVar("_Exp", bound="_Experimentish")
"""TypeVar for the concrete type of an experiment-like object."""


class ExperimentAxisQuery(Generic[_Exp]):
    """Axis-based query against a SOMA Experiment.

    ExperimentAxisQuery allows easy selection and extraction of data from a
    single :class:`Measurement` in an :class:`Experiment`, by obs/var (axis) coordinates
    and/or value filter.

    The primary use for this class is slicing :class:`Experiment` ``X`` layers by obs or
    var value and/or coordinates. Slicing on :class:`SparseNDArray` ``X`` matrices is
    supported; :class:`DenseNDArray` is not supported at this time.

    IMPORTANT: this class is not thread-safe.

    IMPORTANT: this query class assumes it can store the full result of both
    axis dataframe queries in memory, and only provides incremental access to
    the underlying X NDArray. API features such as ``n_obs`` and ``n_vars``
    codify this in the API.

    IMPORTANT: you must call ``close()`` on any instance of this class to
    release underlying resources. The ExperimentAxisQuery is a context manager,
    and it is recommended that you use the following pattern to make this easy
    and safe::

        with ExperimentAxisQuery(...) as query:
            ...

    This base query implementation is designed to work against any SOMA
    implementation that fulfills the basic APIs. A SOMA implementation may
    include a custom query implementation optimized for its own use.

    Lifecycle: maturing
    """

    def __init__(
        self,
        experiment: _Exp,
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
        self._indexer = AxisIndexer(self)
        self._threadpool_: Optional[futures.ThreadPoolExecutor] = None

    def obs(
        self,
        *,
        column_names: Optional[Sequence[str]] = None,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: options.ResultOrderStr = _RO_AUTO,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> data.ReadIter[pa.Table]:
        """Returns ``obs`` as an `Arrow table
        <https://arrow.apache.org/docs/python/generated/pyarrow.Table.html>`_
        iterator.

        Lifecycle: maturing
        """
        obs_query = self._matrix_axis_query.obs
        return self._obs_df.read(
            obs_query.coords,
            value_filter=obs_query.value_filter,
            column_names=column_names,
            batch_size=batch_size,
            partitions=partitions,
            result_order=result_order,
            platform_config=platform_config,
        )

    def var(
        self,
        *,
        column_names: Optional[Sequence[str]] = None,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: options.ResultOrderStr = _RO_AUTO,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> data.ReadIter[pa.Table]:
        """Returns ``var`` as an `Arrow table
        <https://arrow.apache.org/docs/python/generated/pyarrow.Table.html>`_
        iterator.

        Lifecycle: maturing
        """
        var_query = self._matrix_axis_query.var
        return self._var_df.read(
            var_query.coords,
            value_filter=var_query.value_filter,
            column_names=column_names,
            batch_size=batch_size,
            partitions=partitions,
            result_order=result_order,
            platform_config=platform_config,
        )

    def obs_joinids(self) -> pa.Array:
        """Returns ``obs`` ``soma_joinids`` as an Arrow array.

        Lifecycle: maturing
        """
        return self._joinids.obs

    def var_joinids(self) -> pa.Array:
        """Returns ``var`` ``soma_joinids`` as an Arrow array.

        Lifecycle: maturing
        """
        return self._joinids.var

    @property
    def n_obs(self) -> int:
        """The number of ``obs`` axis query results.

        Lifecycle: maturing
        """
        return len(self.obs_joinids())

    @property
    def n_vars(self) -> int:
        """The number of ``var`` axis query results.

        Lifecycle: maturing
        """
        return len(self.var_joinids())

    @property
    def indexer(self) -> "AxisIndexer":
        """A ``soma_joinid`` indexer for both ``obs`` and ``var`` axes.

        Lifecycle: maturing
        """
        return self._indexer

    def X(
        self,
        layer_name: str,
        *,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: options.ResultOrderStr = _RO_AUTO,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> data.SparseRead:
        """Returns an ``X`` layer as a sparse read.

        Args:
            layer_name: The X layer name to return.
            batch_size: The size of batches that should be returned from a read.
                See :class:`options.BatchSize` for details.
            partitions: Specifies that this is part of a partitioned read,
                and which partition to include, if present.
            result_order: the order to return results, specified as a
                :class:`~options.ResultOrder` or its string value.

        Lifecycle: maturing
        """
        try:
            x_layer = self._ms.X[layer_name]
        except KeyError as ke:
            raise KeyError(f"{layer_name} is not present in X") from ke
        if not isinstance(x_layer, data.SparseNDArray):
            raise TypeError("X layers may only be sparse arrays")

        self._joinids.preload(self._threadpool)
        return x_layer.read(
            (self._joinids.obs, self._joinids.var),
            batch_size=batch_size,
            partitions=partitions,
            result_order=result_order,
            platform_config=platform_config,
        )

    def obsp(self, layer: str) -> data.SparseRead:
        """Returns an ``obsp`` layer as a sparse read.

        Lifecycle: maturing
        """
        return self._axisp_inner(_Axis.OBS, layer)

    def varp(self, layer: str) -> data.SparseRead:
        """Returns a ``varp`` layer as a sparse read.

        Lifecycle: maturing
        """
        return self._axisp_inner(_Axis.VAR, layer)

    def obsm(self, layer: str) -> data.SparseRead:
        """Returns an ``obsm`` layer as a sparse read.
        Lifecycle: experimental
        """
        return self._axism_inner(_Axis.OBS, layer)

    def varm(self, layer: str) -> data.SparseRead:
        """Returns a ``varm`` layer as a sparse read.
        Lifecycle: experimental
        """
        return self._axism_inner(_Axis.VAR, layer)

    def to_anndata(
        self,
        X_name: str,
        *,
        column_names: Optional[AxisColumnNames] = None,
        X_layers: Sequence[str] = (),
        obsm_layers: Sequence[str] = (),
        obsp_layers: Sequence[str] = (),
        varm_layers: Sequence[str] = (),
        varp_layers: Sequence[str] = (),
    ) -> anndata.AnnData:
        """
        Executes the query and return result as an ``AnnData`` in-memory object.

        Args:
            X_name: The X layer to read and return in the ``X`` slot.
            column_names: The columns in the ``var`` and ``obs`` dataframes
                to read.
            X_layers: Additional X layers to read and return
                in the ``layers`` slot.
            obsm_layers:
                Additional obsm layers to read and return in the obsm slot.
            obsp_layers:
                Additional obsp layers to read and return in the obsp slot.
            varm_layers:
                Additional varm layers to read and return in the varm slot.
            varp_layers:
                Additional varp layers to read and return in the varp slot.

        Lifecycle: maturing
        """
        return self._read(
            X_name,
            column_names=column_names or AxisColumnNames(obs=None, var=None),
            X_layers=X_layers,
            obsm_layers=obsm_layers,
            obsp_layers=obsp_layers,
            varm_layers=varm_layers,
            varp_layers=varp_layers,
        ).to_anndata()

    # Context management

    def close(self) -> None:
        """Releases resources associated with this query.

        This method must be idempotent.

        Lifecycle: maturing
        """
        # Because this may be called during ``__del__`` when we might be getting
        # disassembled, sometimes ``_threadpool_`` is simply missing.
        # Only try to shut it down if it still exists.
        pool = getattr(self, "_threadpool_", None)
        if pool is None:
            return
        pool.shutdown()
        self._threadpool_ = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def __del__(self) -> None:
        """Ensure that we're closed when our last ref disappears."""
        self.close()
        # If any superclass in our MRO has a __del__, call it.
        sdel = getattr(super(), "__del__", lambda: None)
        sdel()

    # Internals

    def _read(
        self,
        X_name: str,
        *,
        column_names: AxisColumnNames,
        X_layers: Sequence[str],
        obsm_layers: Sequence[str] = (),
        obsp_layers: Sequence[str] = (),
        varm_layers: Sequence[str] = (),
        varp_layers: Sequence[str] = (),
    ) -> "_AxisQueryResult":
        """Reads the entire query result in memory.


        This is a low-level routine intended to be used by loaders for other
        in-core formats, such as AnnData, which can be created from the
        resulting objects.

        Args:
            X_name: The X layer to read and return in the ``X`` slot.
            column_names: The columns in the ``var`` and ``obs`` dataframes
                to read.
            X_layers: Additional X layers to read and return
                in the ``layers`` slot.
            obsm_layers:
                Additional obsm layers to read and return in the obsm slot.
            obsp_layers:
                Additional obsp layers to read and return in the obsp slot.
            varm_layers:
                Additional varm layers to read and return in the varm slot.
            varp_layers:
                Additional varp layers to read and return in the varp slot.
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

        def _read_axis_mappings(fn, axis, keys: Sequence[str]) -> Dict[str, np.ndarray]:
            return {key: fn(axis, key) for key in keys}

        obsm_ft = self._threadpool.submit(
            _read_axis_mappings, self._axism_inner_ndarray, _Axis.OBS, obsm_layers
        )
        obsp_ft = self._threadpool.submit(
            _read_axis_mappings, self._axisp_inner_ndarray, _Axis.OBS, obsp_layers
        )
        varm_ft = self._threadpool.submit(
            _read_axis_mappings, self._axism_inner_ndarray, _Axis.VAR, varm_layers
        )
        varp_ft = self._threadpool.submit(
            _read_axis_mappings, self._axisp_inner_ndarray, _Axis.VAR, varp_layers
        )

        obs_table, var_table = self._read_both_axes(column_names)

        x_matrices = {
            _xname: _fast_csr.read_scipy_csr(
                all_x_arrays[_xname], self.obs_joinids(), self.var_joinids()
            )
            for _xname in all_x_arrays
        }

        x = x_matrices.pop(X_name)

        obs = obs_table.to_pandas()
        obs.index = obs.index.astype(str)

        var = var_table.to_pandas()
        var.index = var.index.astype(str)

        return _AxisQueryResult(
            obs=obs,
            var=var,
            X=x,
            obsm=obsm_ft.result(),
            obsp=obsp_ft.result(),
            varm=varm_ft.result(),
            varp=varp_ft.result(),
            X_layers=x_matrices,
        )

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
        column_names = axis_column_names.get(axis.value)

        axis_df = axis.getattr_from(self, pre="_", suf="_df")
        assert isinstance(axis_df, data.DataFrame)
        axis_query = axis.getattr_from(self._matrix_axis_query)

        # If we can cache join IDs, prepare to add them to the cache.
        joinids_cached = self._joinids._is_cached(axis)
        query_columns = column_names
        added_soma_joinid_to_columns = False
        if (
            not joinids_cached
            and column_names is not None
            and "soma_joinid" not in column_names
        ):
            # If we want to fill the join ID cache, ensure that we query the
            # soma_joinid column so that it is included in the results.
            # We'll filter it out later.
            query_columns = ["soma_joinid"] + list(column_names)
            added_soma_joinid_to_columns = True

        # Do the actual query.
        arrow_table = axis_df.read(
            axis_query.coords,
            value_filter=axis_query.value_filter,
            column_names=query_columns,
        ).concat()

        # Update the cache if needed. We can do this because no matter what
        # other columns are queried for, the contents of the ``soma_joinid``
        # column will be the same and can be safely stored.
        if not joinids_cached:
            setattr(
                self._joinids,
                axis.value,
                arrow_table.column("soma_joinid").combine_chunks(),
            )

        # Drop soma_joinid column if we added it solely for use in filling
        # the joinid cache.
        if added_soma_joinid_to_columns:
            arrow_table = arrow_table.drop(["soma_joinid"])
        return arrow_table

    def _axisp_inner(
        self,
        axis: "_Axis",
        layer: str,
    ) -> data.SparseRead:
        p_name = f"{axis.value}p"
        try:
            axisp = axis.getitem_from(self._ms, suf="p")
        except KeyError as ke:
            raise ValueError(f"Measurement does not contain {p_name} data") from ke

        try:
            ap_layer = axisp[layer]
        except KeyError as ke:
            raise ValueError(f"layer {layer!r} is not available in {p_name}") from ke
        if not isinstance(ap_layer, data.SparseNDArray):
            raise TypeError(
                f"Unexpected SOMA type {type(ap_layer).__name__}"
                f" stored in {p_name} layer {layer!r}"
            )

        joinids = axis.getattr_from(self._joinids)
        return ap_layer.read((joinids, joinids))

    def _axism_inner(
        self,
        axis: "_Axis",
        layer: str,
    ) -> data.SparseRead:
        m_name = f"{axis.value}m"

        try:
            axism = axis.getitem_from(self._ms, suf="m")
        except KeyError:
            raise ValueError(f"Measurement does not contain {m_name} data") from None

        try:
            axism_layer = axism[layer]
        except KeyError as ke:
            raise ValueError(f"layer {layer!r} is not available in {m_name}") from ke

        if not isinstance(axism_layer, data.SparseNDArray):
            raise TypeError(f"Unexpected SOMA type stored in '{m_name}' layer")

        joinids = axis.getattr_from(self._joinids)
        return axism_layer.read((joinids, slice(None)))

    def _convert_to_ndarray(
        self, axis: "_Axis", table: pa.Table, n_row: int, n_col: int
    ) -> np.ndarray:
        indexer: pd.Index = axis.getattr_from(self.indexer, pre="by_")
        idx = indexer(table["soma_dim_0"])
        z = np.zeros(n_row * n_col, dtype=np.float32)
        np.put(z, idx * n_col + table["soma_dim_1"], table["soma_data"])
        return z.reshape(n_row, n_col)

    def _axisp_inner_ndarray(
        self,
        axis: "_Axis",
        layer: str,
    ) -> np.ndarray:
        n_row = n_col = len(axis.getattr_from(self._joinids))

        table = self._axisp_inner(axis, layer).tables().concat()
        return self._convert_to_ndarray(axis, table, n_row, n_col)

    def _axism_inner_ndarray(
        self,
        axis: "_Axis",
        layer: str,
    ) -> np.ndarray:
        axism = axis.getitem_from(self._ms, suf="m")

        _, n_col = axism[layer].shape
        n_row = len(axis.getattr_from(self._joinids))

        table = self._axism_inner(axis, layer).tables().concat()
        return self._convert_to_ndarray(axis, table, n_row, n_col)

    @property
    def _obs_df(self) -> data.DataFrame:
        return self.experiment.obs

    @property
    def _ms(self) -> measurement.Measurement:
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
    """The result of running :meth:`ExperimentAxisQuery.read`. Private."""

    obs: pd.DataFrame
    """Experiment.obs query slice, as a pandas DataFrame"""
    var: pd.DataFrame
    """Experiment.ms[...].var query slice, as a pandas DataFrame"""
    X: sparse.csr_matrix
    """Experiment.ms[...].X[...] query slice, as an SciPy sparse.csr_matrix """
    X_layers: Dict[str, sparse.csr_matrix] = attrs.field(factory=dict)
    """Any additional X layers requested, as SciPy sparse.csr_matrix(s)"""
    obsm: Dict[str, np.ndarray] = attrs.field(factory=dict)
    """Experiment.obsm query slice, as a numpy ndarray"""
    obsp: Dict[str, np.ndarray] = attrs.field(factory=dict)
    """Experiment.obsp query slice, as a numpy ndarray"""
    varm: Dict[str, np.ndarray] = attrs.field(factory=dict)
    """Experiment.varm query slice, as a numpy ndarray"""
    varp: Dict[str, np.ndarray] = attrs.field(factory=dict)
    """Experiment.varp query slice, as a numpy ndarray"""

    def to_anndata(self) -> anndata.AnnData:
        return anndata.AnnData(
            X=self.X,
            obs=self.obs,
            var=self.var,
            obsm=(self.obsm or None),
            obsp=(self.obsp or None),
            varm=(self.varm or None),
            varp=(self.varp or None),
            layers=(self.X_layers or None),
        )


class _Axis(enum.Enum):
    OBS = "obs"
    VAR = "var"

    @property
    def value(self) -> Literal["obs", "var"]:
        return super().value

    @overload
    def getattr_from(self, __source: "_HasObsVar[_T]") -> "_T":
        ...

    @overload
    def getattr_from(
        self, __source: Any, *, pre: Literal[""], suf: Literal[""]
    ) -> object:
        ...

    @overload
    def getattr_from(self, __source: Any, *, pre: str = ..., suf: str = ...) -> object:
        ...

    def getattr_from(self, __source: Any, *, pre: str = "", suf: str = "") -> object:
        """Equivalent to ``something.<pre><obs/var><suf>``."""
        return getattr(__source, pre + self.value + suf)

    def getitem_from(
        self, __source: Mapping[str, "_T"], *, pre: str = "", suf: str = ""
    ) -> "_T":
        """Equivalent to ``something[pre + "obs"/"var" + suf]``."""
        return __source[pre + self.value + suf]


@attrs.define(frozen=True)
class _MatrixAxisQuery:
    """The per-axis user query definition. Private."""

    obs: axis.AxisQuery
    var: axis.AxisQuery


@attrs.define
class _JoinIDCache:
    """A cache for per-axis join ids in the query. Private."""

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
        axq.coords,
        value_filter=axq.value_filter,
        column_names=["soma_joinid"],
    ).concat()
    return tbl.column("soma_joinid").combine_chunks()


_Numpyable = Union[pa.Array, pa.ChunkedArray, npt.NDArray[np.int64]]
"""Things that can be converted to a NumPy array."""


@attrs.define
class AxisIndexer:
    """
    Given a query, provides index-building services for obs/var axis.

    Lifecycle: maturing
    """

    query: ExperimentAxisQuery
    _cached_obs: Optional[pd.Index] = None
    _cached_var: Optional[pd.Index] = None

    @property
    def _obs_index(self) -> pd.Index:
        """Private. Return an index for the ``obs`` axis."""
        if self._cached_obs is None:
            self._cached_obs = pd.Index(data=self.query.obs_joinids().to_numpy())
        return self._cached_obs

    @property
    def _var_index(self) -> pd.Index:
        """Private. Return an index for the ``var`` axis."""
        if self._cached_var is None:
            self._cached_var = pd.Index(data=self.query.var_joinids().to_numpy())
        return self._cached_var

    def by_obs(self, coords: _Numpyable) -> npt.NDArray[np.intp]:
        """Reindex the coords (soma_joinids) over the ``obs`` axis."""
        return self._obs_index.get_indexer(_to_numpy(coords))

    def by_var(self, coords: _Numpyable) -> npt.NDArray[np.intp]:
        """Reindex for the coords (soma_joinids) over the ``var`` axis."""
        return self._var_index.get_indexer(_to_numpy(coords))


def _to_numpy(it: _Numpyable) -> np.ndarray:
    if isinstance(it, np.ndarray):
        return it
    return it.to_numpy()


#
# Type shenanigans
#

_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)


class _Experimentish(Protocol):
    """The API we need from an Experiment."""

    @property
    def ms(self) -> Mapping[str, measurement.Measurement]:
        ...

    @property
    def obs(self) -> data.DataFrame:
        ...


class _HasObsVar(Protocol[_T_co]):
    """Something which has an ``obs`` and ``var`` field.

    Used to give nicer type inference in :meth:`_Axis.getattr_from`.
    """

    @property
    def obs(self) -> _T_co:
        ...

    @property
    def var(self) -> _T_co:
        ...
