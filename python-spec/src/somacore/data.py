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
    TypeVar,
    Union,
)

import pyarrow as pa
from typing_extensions import Final, Literal, Self

from . import base
from . import options

_RO_AUTO = options.ResultOrder.AUTO


class DataFrame(base.SOMAObject, metaclass=abc.ABCMeta):
    """A multi-column table with a user-defined schema."""

    __slots__ = ()
    soma_type: Final = "SOMADataFrame"  # type: ignore[misc]

    # Lifecycle

    @classmethod
    @abc.abstractmethod
    def create(
        cls,
        uri: str,
        *,
        schema: pa.Schema,
        index_column_names: Sequence[str] = (options.SOMA_JOINID,),
        platform_config: Optional[options.PlatformConfig] = None,
        context: Optional[Any] = None,
    ) -> Self:
        """Creates a new DataFrame at the given URI.

        :param uri: The URI where the DataFrame will be created.
        :param schema: Arrow schema defining the per-column schema. This schema
            must define all columns, including columns to be named as index
            columns.  If the schema includes types unsupported by the SOMA
            implementation, an error will be raised.
        :param index_column_names: A list of column names to use as user-defined
            index columns (e.g., ``['cell_type', 'tissue_type']``).
            All named columns must exist in the schema, and at least one
            index column name is required.
        """
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

        :param coords: for each index dimension, which rows to read.
            Defaults to ``None``, meaning no constraint -- all IDs.
        :param column_names: the named columns to read and return.
            Defaults to ``None``, meaning no constraint -- all column names.
        :param partitions: an optional ``ReadPartitions`` hint to indicate
            how results should be organized.
        :param result_order: order of read results.
            This can be one of 'row-major', 'col-major', or 'auto'.
        :param value_filter: an optional [value filter] to apply to the results.
            Defaults to no filter.

        **Indexing:**

        Indexing is performed on a per-column basis for each indexed column.
        To specify dimensions:

        - A sequence of coordinates is accepted, one per indexed dimension.
        - The sequence length must be less than or equal to the number of
          indexed dimensions.
        - If the sequence is shorter than the number of indexed coordinates,
          then no constraint (i.e. ``None``) is used for the remaining
          indexed dimensions.
        - Specifying ``None`` or an empty sequence (e.g. ``()``) represents
          no constraints over any dimension, returning the entire dataset.
          TODO: https://github.com/single-cell-data/TileDB-SOMA/pull/910

        Each dimension may be indexed as follows:

        - ``None`` or ``slice(None)`` places no constraint on the dimension.
        - Coordinates can be specified as a scalar value, a Python sequence
          (``list``, ``tuple``, etc.), a ``ndarray``, an Arrow array, and
          similar objects (as defined by ``SparseDFCoords``).
        - Slices are doubly inclusive: ``slice(2, 4)`` means ``[2, 3, 4]``,
          not ``[2, 3]``.  Slice *steps* may not be used: ``slice(10, 20, 2)``
          is invalid.  ``slice(None)`` places no constraint on the dimension.
          Half-specified slices like ``slice(None, 99)`` and ``slice(5, None)``
          specify all indices up to and including that value, and all indices
          starting from and including the value.
        - Negative indexing is not supported.
          TODO: What if the domain includes negative numbers?
          Negative values are treated as ordinary indices, e.g. ``slice(-1, 5)``
          represents all indices between −1 and 5 (inclusive).
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def write(
        self,
        values: Union[pa.RecordBatch, pa.Table],
        *,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> None:
        """Writes the data from an Arrow table to the persistent object.

        As duplicate index values are not allowed, index values already present
        in the object are overwritten and new index values are added.

        [lifecycle: experimental]

        :param values: An Arrow table containing all columns, including
            the index columns. The schema for the values must match
            the schema for the ``DataFrame``.
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


class NDArray(base.SOMAObject, metaclass=abc.ABCMeta):
    """Common behaviors of N-dimensional arrays of a single primitive type."""

    __slots__ = ()

    # Lifecycle

    @classmethod
    @abc.abstractmethod
    def create(
        cls,
        uri: str,
        *,
        type: pa.DataType,
        shape: Sequence[int],
        platform_config: Optional[options.PlatformConfig] = None,
        context: Optional[Any] = None,
    ) -> Self:
        """Creates a new ND array of the current type at the given URI.

        :param uri: The URI where the array will be created.
        :param type: The Arrow type to store in the array.
            If the type is unsupported, an error will be raised.
        :param shape: The length of each dimension as a sequence,
            e.g. ``(100, 10)``. All lengths must be in the postive int64 range.
        """
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
        """Reads the specified subarray from this DenseNDArray as a Tensor.

        Coordinates must specify a contiguous subarray, and the number of
        coordinates must be less than or equal to the number of dimensions.
        For example, if the array is 10×20, acceptable values of ``coords``
        include ``()``, ``(3, 4)``, ``[slice(5, 10)]``, and
        ``[slice(5, 10), slice(6, 12)]``.  Slice indices are doubly-inclusive.

        :param coords: A per-dimension sequence of coordinates defining
            the range to read.
        :param batch_size: The size of batches that should be returned
            from a read. See :class:`options.BatchSize` for details.
            XXX How does this work if this returns a single Tensor?
        :param partitions: Specifies that this is part of a partitioned read,
            and which partition to include, if present.
        :param result_order: The order to return the results in.

        **Indexing:**

        Indexing is performed on a per-dimension basis.

        - A sequence of coordinates is accepted, one per dimension.
        - The sequence length must be less than the number of dimensions.
        - If the sequence is shorter than the number of dimensions, the
          remaining dimensions are unconstrained. (Thus, if an empty sequence
          is provided, the entire array will be returned.)

        Each dimension may be indexed by value or slice:

        - Slices are doubly-inclusive.
        - Half-specified slices include all data up to or starting from the
          specified bound, inclusive.
        - Negative indexing is unsupported.
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

        The subarray written is defined by ``coords`` and ``values``. This will
        overwrite existing values in the array.

        :param coords: A per-dimension tuple of scalars or slices
            defining the bounds of the subarray to be written.
        :param values: The values to be written to the subarray.  Must have
            the same shape as ``coords``, and matching type to the DenseNDArray.
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
        """Reads a subset this DenseNDArray in batches.

        Values returned are a :class:`SparseRead` object which can be converted
        to any number of formats::

            some_dense_array.read(...).tables()
            # -> an iterator of Arrow Tables
            some_dense_array.read(...).csrs().all()
            # -> a single flattened sparse CSR matrix

        :param coords: A per-dimension sequence of coordinates defining
            the range to be read.
        :param batch_size: The size of batches that should be returned
            from a read. See :class:`options.BatchSize` for details.
        :param partitions: Specifies that this is part of a partitioned read,
            and which partition to include, if present.
        :param result_order: The order to return the results in.

        **Indexing:**

        Indexing is performed on a per-dimension basis.

        - A sequence of coordinates is accepted, one per dimension.
        - The sequence length must be less than the number of dimensions.
        - If the sequence is shorter than the number of dimensions, the
          remaining dimensions are unconstrained.
        - Specifying ``None`` or an empty sequence will return the entire array.

        Each dimension may be indexed as follows:

        - ``None`` or ``slice(None)`` places no constraint on the dimension.
        - Coordinates can be specified as a scalar value, a Python sequence
          (``list``, ``tuple``, etc.), a ``ndarray``, an Arrow array, and
          similar objects (as defined by ``SparseNDCoords``).
        - Slices are doubly inclusive: ``slice(2, 4)`` means ``[2, 3, 4]``,
          not ``[2, 3]``.  Slice *steps* may not be used: ``slice(10, 20, 2)``
          is invalid.  ``slice(None)`` places no constraint on the dimension.
          Half-specified slices like ``slice(None, 99)`` and ``slice(5, None)``
          specify all indices up to and including that value, and all indices
          starting from and including the value.
        - Negative indexing is not supported.
        """

    @abc.abstractmethod
    def write(
        self,
        values: SparseArrowData,
        *,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> None:
        """Writes a Tensor to a subarray of the persistent object.

        :param values: The values to write to the array.

        **Value types:**

        Arrow sparse tensor: the coordinates in the tensor are interpreted as
        the coordinates to write to.  Supports the *experimental* types
        SparseCOOTensor, SparseCSRMatrix and SparseCSCMatrix. There is currently
        no support for Arrow SparseCSFTensor or dense Tensor.

        Arrow table: a COO table, with columns named ``soma_dim_0``, ...,
        ``soma_dim_N`` and ``soma_data``, to be written to the array.

        """
        raise NotImplementedError()

    @property
    def nnz(self) -> int:
        """The number of values stored in the array, including explicit zeros."""
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
