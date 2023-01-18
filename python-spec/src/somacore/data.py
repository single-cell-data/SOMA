"""Definitions of data storage interfaces for SOMA implementations.

SOMA users should ordinarily not need to import this module directly; relevant
members will be exported to the ``somacore`` namespace.

Default values are provided here as a reference for implementors.
"""

import abc
from typing import Iterator, Optional, Sequence, Tuple, TypeVar, Union

import pyarrow
from typing_extensions import Final

from somacore import base
from somacore import options

_RO_AUTO = options.ResultOrder.AUTO


class DataFrame(base.SOMAObject, metaclass=abc.ABCMeta):
    """A multi-column table with a user-defined schema."""

    __slots__ = ()

    # Data operations

    @abc.abstractmethod
    def read(
        self,
        coords: options.SparseDFCoords,
        column_names: Optional[Sequence[str]] = None,
        *,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: options.StrOr[options.ResultOrder] = _RO_AUTO,
        value_filter: Optional[str] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> "ReadIter[pyarrow.Table]":
        """Reads a user-defined slice of data into Arrow tables.

        TODO: Further per-param documentation.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def write(
        self,
        values: Union[pyarrow.RecordBatch, pyarrow.Table],
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> None:
        """Writes values to the data store.

        TODO: Further per-param documentation.
        """
        raise NotImplementedError()

    # Metadata operations

    @property
    @abc.abstractmethod
    def schema(self) -> pyarrow.Schema:
        """The schema of the data in this dataframe."""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def index_column_names(self) -> Tuple[str, ...]:
        """The names of the index (dimension) columns."""
        raise NotImplementedError()

    # Basic operations

    soma_type: Final = "SOMADataFrame"


class NDArray(base.SOMAObject, metaclass=abc.ABCMeta):
    """Common behaviors of N-dimensional arrays of a single primitive type."""

    __slots__ = ()

    # Metadata operations

    @property
    @abc.abstractmethod
    def shape(self) -> Tuple[int, ...]:
        """The length of each dimension of this array."""
        raise NotImplementedError()

    @property
    def ndim(self) -> int:
        """The number of dimensions in this array."""
        return len(self.shape)

    @property
    @abc.abstractmethod
    def schema(self) -> pyarrow.Schema:
        """The schema of the data in this array."""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def is_sparse(self) -> bool:
        """True if this array is sparse. False if this array is dense."""
        raise NotImplementedError()


class DenseNDArray(NDArray, metaclass=abc.ABCMeta):
    """A N-dimensional array stored densely."""

    __slots__ = ()

    @abc.abstractmethod
    def read(
        self,
        coords: options.DenseNDCoords,
        *,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: options.StrOr[options.ResultOrder] = _RO_AUTO,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> pyarrow.Tensor:
        """Reads the specified subarray from this NDArray as a Tensor.

        TODO: Additional per-param documentation.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def write(
        self,
        coords: options.DenseNDCoords,
        values: pyarrow.Tensor,
        *,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> None:
        """Writes a Tensor to a subarray of the persistent object.

        TODO: Additional per-param documentation.
        """
        raise NotImplementedError()

    is_sparse: Final = False
    soma_type: Final = "SOMADenseNDArray"


SparseArrowData = Union[
    pyarrow.SparseCSCMatrix,
    pyarrow.SparseCSRMatrix,
    pyarrow.SparseCOOTensor,
    pyarrow.Table,
]
"""Any of the sparse data storages provided by Arrow."""


class SparseNDArray(NDArray, metaclass=abc.ABCMeta):
    """A N-dimensional array stored sparsely."""

    __slots__ = ()

    @abc.abstractmethod
    def read(
        self,
        coords: options.SparseNDCoords,
        *,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: options.StrOr[options.ResultOrder] = _RO_AUTO,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> "SparseRead":
        """Reads a subset of the object in one or more batches.

        Values returned are a :class:`SparseRead` object which can be converted
        to any number of formats::

            some_dense_array.read(...).tables()
            # -> an iterator of Arrow Tables
            some_dense_array.read(...).csrs().all()
            # -> a single flattened sparse CSR matrix

        TODO: Additional per-param documentation.
        """

    @abc.abstractmethod
    def write(
        self,
        values: SparseArrowData,
        *,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> None:
        """Writes a Tensor to a subarray of the persistent object.

        TODO: Additional per-param documentation.
        """
        raise NotImplementedError()

    @property
    def nnz(self) -> int:
        """The number of values stored in the array, including explicit zeros.

        For dense arrays, this will be the total size of the array.
        """
        raise NotImplementedError()

    is_sparse: Final = True
    soma_type: Final = "SOMASparseNDArray"


#
# Read types
#

_T = TypeVar("_T")


# Sparse reads are returned as an iterable structure:


class ReadIter(Iterator[_T], metaclass=abc.ABCMeta):
    """SparseRead result iterator allowing users to flatten the iteration."""

    # __iter__ is already implemented as `return self` in Iterator.
    # SOMA implementations must implement __next__.

    @abc.abstractmethod
    def concat(self) -> _T:
        """Returns all the requested data in a single operation.

        If some data has already been retrieved using ``next``, this will return
        the rest of the data after that is already returned.
        """
        raise NotImplementedError()


class SparseRead:
    """Intermediate type to choose result format when reading a sparse array.

    A query may not be able to return all of these formats. The concrete result
    may raise a ``NotImplementedError`` or may choose to raise a different
    exception (likely a ``TypeError``) containing more specific information
    about why the given format is not supported.
    """

    def coos(self) -> ReadIter[pyarrow.SparseCOOTensor]:
        raise NotImplementedError()

    def cscs(self) -> ReadIter[pyarrow.SparseCSCMatrix]:
        raise NotImplementedError()

    def csrs(self) -> ReadIter[pyarrow.SparseCSRMatrix]:
        raise NotImplementedError()

    def dense_tensors(self) -> ReadIter[pyarrow.Tensor]:
        raise NotImplementedError()

    def record_batches(self) -> ReadIter[pyarrow.RecordBatch]:
        raise NotImplementedError()

    def tables(self) -> ReadIter[pyarrow.Table]:
        raise NotImplementedError()
