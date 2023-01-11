import abc
import contextlib
from typing import Any, Optional, Sequence, TypedDict

import anndata
import pyarrow as pa

from somacore import data


class AxisColumnNames(TypedDict, total=False):
    """Specifies column names for experiment axis query read operations."""

    obs: Optional[Sequence[str]]
    """obs columns to use. All columns if ``None`` or not present."""
    var: Optional[Sequence[str]]
    """var columns to use. All columns if ``None`` or not present."""


class ExperimentAxisQuery(contextlib.AbstractContextManager, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def obs(
        self, *, column_names: Optional[Sequence[str]] = None
    ) -> data.ReadIter[pa.Table]:
        """Returns ``obs`` as an Arrow table iterator."""
        raise NotImplementedError()

    @abc.abstractmethod
    def var(
        self, *, column_names: Optional[Sequence[str]] = None
    ) -> data.ReadIter[pa.Table]:
        """Returns ``var`` as an Arrow table iterator."""
        raise NotImplementedError()

    @abc.abstractmethod
    def obs_joinids(self) -> pa.Array:
        """Returns ``obs`` ``soma_joinids`` as an Arrow array."""
        raise NotImplementedError()

    @abc.abstractmethod
    def var_joinids(self) -> pa.Array:
        """Returns ``var`` ``soma_joinids`` as an Arrow array."""
        raise NotImplementedError()

    @property
    def n_obs(self) -> int:
        """The number of ``obs`` axis query results."""
        return len(self.obs_joinids())

    @property
    def n_vars(self) -> int:
        """The number of ``var`` axis query results."""
        return len(self.var_joinids())

    @abc.abstractmethod
    def X(self, layer_name: str) -> data.SparseRead:
        """Returns an ``X`` layer as ``SparseRead`` data.

        :param layer_name: The X layer name to return.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def obsp(self, layer: str) -> data.SparseRead:
        """Return an ``obsp`` layer as a SparseNDArrayRead"""
        raise NotImplementedError()

    @abc.abstractmethod
    def varp(self, layer: str) -> data.SparseRead:
        """Return an ``varp`` layer as a SparseNDArrayRead"""
        raise NotImplementedError()

    @abc.abstractmethod
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
        raise NotImplementedError()

    # Context management

    @abc.abstractmethod
    def close(self) -> None:
        """Releases resources associated with this query.

        This method must be idempotent.
        """
        raise NotImplementedError()

    def __exit__(self, *_: Any) -> None:
        self.close()

    def __del__(self) -> None:
        """Ensure that we're closed when our last ref disappears."""
        # If any superclass in our MRO has a __del__, call it.
        sdel = getattr(super(), "__del__", lambda: None)
        sdel()
        self.close()
