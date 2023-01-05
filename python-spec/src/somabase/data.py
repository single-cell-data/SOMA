"""Definitions of data storage interfaces for SOMA implementations.

SOMA users should ordinarily not need to import this module directly; relevant
members will be exported to the ``somabase`` namespace.
"""

import abc
from typing import Any, Iterator, Optional, Sequence, Tuple, TypeVar, Union

import pyarrow
from typing_extensions import Final

from somabase import base
from somabase import options


class DataFrame(base.SOMAObject, metaclass=abc.ABCMeta):
    """A multi-column table with a user-defined schema."""

    __slots__ = ()

    # Data operations

    @abc.abstractmethod
    def read(
        self,
        ids,  # TODO: Specify type
        column_names: Optional[Sequence[str]] = None,
        *,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: Optional[options.ResultOrder] = None,
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
    def ndims(self) -> int:
        """The Number of Dimensions in this array."""
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
        coords: options.ReadCoords,
        *,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: options.ResultOrder = None,  # XXX: Set default
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> pyarrow.Tensor:
        """Reads the specified subarray from this NDArray as a Tensor.

        TODO: Additional per-param documentation.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def write(
        self,
        coords: options.ReadCoords,
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


class SparseNDArray(NDArray, metaclass=abc.ABCMeta):
    """A N-dimensional array stored sparsely."""

    __slots__ = ()

    @abc.abstractmethod
    def read(
        self,
        slices: Any,  # TODO: Define this type.
        *,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: options.ResultOrder = None,  # XXX set default
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
        values: pyarrow.Tensor,
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

    # __iter__ is already implemented as `return self` in Iterator
    # SOMA implementations must implement __next__.

    # XXX: Considering the name "flat" here too.
    @abc.abstractmethod
    def all(self) -> _T:
        """Returns all the requested data in a single operation."""
        raise NotImplementedError()


class SparseRead(metaclass=abc.ABCMeta):
    """Intermediate type to allow users to format when reading a sparse array."""

    @abc.abstractmethod
    def coos(self) -> ReadIter[pyarrow.SparseCOOTensor]:
        raise NotImplementedError()

    @abc.abstractmethod
    def cscs(self) -> ReadIter[pyarrow.SparseCSCMatrix]:
        raise NotImplementedError()

    @abc.abstractmethod
    def csrs(self) -> ReadIter[pyarrow.SparseCSRMatrix]:
        raise NotImplementedError()

    # XXX Does this need to return a ReadIter of Tuple[coordinates, Tensor]?
    @abc.abstractmethod
    def dense_tensors(self) -> ReadIter[pyarrow.Tensor]:
        raise NotImplementedError()

    @abc.abstractmethod
    def record_batches(self) -> ReadIter[pyarrow.RecordBatch]:
        raise NotImplementedError()

    @abc.abstractmethod
    def tables(self) -> ReadIter[pyarrow.Table]:
        raise NotImplementedError()
