"""Definitions of data storage interfaces for SOMA implementations.

SOMA users should ordinarily not need to import this module directly; relevant
members will be exported to the ``somacore`` namespace.

Default values are provided here as a reference for implementors.
"""

import abc
from typing import (
    Any,
    ClassVar,
    Iterator,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import pyarrow as pa
from typing_extensions import Final, Literal

from . import base
from . import options

_RO_AUTO = options.ResultOrder.AUTO

_DFT = TypeVar("_DFT", bound="DataFrame")
"""Any implementation of DataFrame."""


class DataFrame(base.SOMAObject, metaclass=abc.ABCMeta):
    """A multi-column table with a user-defined schema."""

    __slots__ = ()
    soma_type: Final = "SOMADataFrame"  # type: ignore[misc]

    # Lifecycle

    @classmethod
    @abc.abstractmethod
    def create(
        cls: Type[_DFT],
        uri: str,
        *,
        schema: pa.Schema,
        index_column_names: Sequence[str] = (options.SOMA_JOINID,),
        platform_config: Optional[options.PlatformConfig] = None,
        context: Optional[Any] = None,
    ) -> _DFT:
        """Creates a new DataFrame."""
        raise NotImplementedError()

    # Data operations

    @abc.abstractmethod
    def read(
        self,
        coords: Optional[options.SparseDFCoords] = None,
        column_names: Optional[Sequence[str]] = None,
        *,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: options.ResultOrderStr = _RO_AUTO,
        value_filter: Optional[str] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> "ReadIter[pa.Table]":
        """Reads a user-defined slice of data into Arrow tables.

        TODO: Further per-param documentation.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def write(
        self,
        values: Union[pa.RecordBatch, pa.Table],
        *,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> None:
        """Writes values to the data store.

        TODO: Further per-param documentation.
        """
        raise NotImplementedError()

    # Metadata operations

    @property
    @abc.abstractmethod
    def schema(self) -> pa.Schema:
        """The schema of the data in this dataframe."""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def index_column_names(self) -> Tuple[str, ...]:
        """The names of the index (dimension) columns."""
        raise NotImplementedError()


_NDT = TypeVar("_NDT", bound="NDArray")
"""Any implementation of NDArray."""


class NDArray(base.SOMAObject, metaclass=abc.ABCMeta):
    """Common behaviors of N-dimensional arrays of a single primitive type."""

    __slots__ = ()

    # Lifecycle

    @classmethod
    @abc.abstractmethod
    def create(
        cls: Type[_NDT],
        uri: str,
        *,
        type: pa.DataType,
        shape: Sequence[int],
        platform_config: Optional[options.PlatformConfig] = None,
        context: Optional[Any] = None,
    ) -> _NDT:
        """Creates a new NDArray at the given URI."""
        raise NotImplementedError()

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
    def schema(self) -> pa.Schema:
        """The schema of the data in this array."""
        raise NotImplementedError()

    is_sparse: ClassVar[Literal[True, False]]
    """True if the array is sparse. False if it is dense."""


class DenseNDArray(NDArray, metaclass=abc.ABCMeta):
    """A N-dimensional array stored densely."""

    __slots__ = ()
    soma_type: Final = "SOMADenseNDArray"  # type: ignore[misc]
    is_sparse: Final = False  # type: ignore[misc]

    @abc.abstractmethod
    def read(
        self,
        coords: options.DenseNDCoords,
        *,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: options.ResultOrderStr = _RO_AUTO,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> pa.Tensor:
        """Reads the specified subarray from this NDArray as a Tensor.

        TODO: Additional per-param documentation.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def write(
        self,
        coords: options.DenseNDCoords,
        values: pa.Tensor,
        *,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> None:
        """Writes a Tensor to a subarray of the persistent object.

        TODO: Additional per-param documentation.
        """
        raise NotImplementedError()


SparseArrowData = Union[
    pa.SparseCSCMatrix,
    pa.SparseCSRMatrix,
    pa.SparseCOOTensor,
    pa.Table,
]
"""Any of the sparse data storages provided by Arrow."""


class SparseNDArray(NDArray, metaclass=abc.ABCMeta):
    """A N-dimensional array stored sparsely."""

    __slots__ = ()
    soma_type: Final = "SOMASparseNDArray"  # type: ignore[misc]
    is_sparse: Final = True  # type: ignore[misc]

    @abc.abstractmethod
    def read(
        self,
        coords: Optional[options.SparseNDCoords] = None,
        *,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: options.ResultOrderStr = _RO_AUTO,
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

    def coos(self) -> ReadIter[pa.SparseCOOTensor]:
        raise NotImplementedError()

    def cscs(self) -> ReadIter[pa.SparseCSCMatrix]:
        raise NotImplementedError()

    def csrs(self) -> ReadIter[pa.SparseCSRMatrix]:
        raise NotImplementedError()

    def dense_tensors(self) -> ReadIter[pa.Tensor]:
        raise NotImplementedError()

    def record_batches(self) -> ReadIter[pa.RecordBatch]:
        raise NotImplementedError()

    def tables(self) -> ReadIter[pa.Table]:
        raise NotImplementedError()
