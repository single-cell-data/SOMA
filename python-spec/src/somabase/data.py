"""Definitions of data storage interfaces for SOMA implementations.

SOMA users should ordinarily not need to import this module directly; relevant
members will be exported to the ``somabase`` namespace.
"""

import abc
from typing import Any, Iterable, Optional, Sequence, Tuple, Union

import attrs
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
    ) -> Iterable[pyarrow.Table]:
        """Reads a user-defined slice of data into Arrow tables."""
        raise NotImplementedError()

    @abc.abstractmethod
    def write(
        self,
        values: Union[pyarrow.RecordBatch, pyarrow.Table],
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> None:
        """Writes values to the data store."""
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


@attrs.define(frozen=True)
class CoordsData:
    """A slice of data returned from a SOMA dense read."""

    coords: Any  # TODO: Define type.
    """The coordinates of the slice that was read."""

    data: pyarrow.Tensor
    """The data that was read."""


class NDArray(base.SOMAObject, metaclass=abc.ABCMeta):
    """Common behaviors of N-dimensional arrays of a single primitive type."""

    __slots__ = ()

    # Data operations (listed alphabetically)

    @abc.abstractmethod
    def read_coo(
        self,
        coords,  # TODO: Specify type.
        *,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: Optional[options.ResultOrder] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> Iterable[pyarrow.SparseCOOTensor]:
        """Reads a subset of this NDArray and returns result batches."""
        raise NotImplementedError()

    @abc.abstractmethod
    def read_csc(
        self,
        coords,  # TODO: Specify type.
        *,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: Optional[options.ResultOrder] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> Iterable[pyarrow.SparseCSCMatrix]:
        """Reads a subset of this NDArray and returns result batches."""
        raise NotImplementedError()

    @abc.abstractmethod
    def read_csr(
        self,
        coords,  # TODO: Specify type.
        *,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: Optional[options.ResultOrder] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> Iterable[pyarrow.SparseCSRMatrix]:
        """Reads a subset of this NDArray and returns result batches."""
        raise NotImplementedError()

    @abc.abstractmethod
    def read_dense(
        self,
        coords,  # TODO: Specify type.
        *,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: Optional[options.ResultOrder] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> Iterable[CoordsData]:
        """Reads a subset of this NDArray and returns result batches."""
        raise NotImplementedError()

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
    def write(
        self,
        coords,  # TODO: Specify type.
        values: pyarrow.Tensor,
        *,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> None:
        """Writes a Tensor to a subarray of the persistent object."""
        raise NotImplementedError()

    is_sparse: Final = False
    soma_type: Final = "SOMADenseNDArray"


class SparseNDArray(NDArray, metaclass=abc.ABCMeta):
    """A N-dimensional array stored sparsely."""

    __slots__ = ()

    @abc.abstractmethod
    def write(
        self,
        values: pyarrow.Tensor,
        *,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> None:
        """Writes a Tensor to a subarray of the persistent object."""
        raise NotImplementedError()

    @property
    def nnz(self) -> int:
        """The number of values stored in the array, including explicit zeros.

        For dense arrays, this will be the total size of the array.
        """
        raise NotImplementedError()

    is_sparse: Final = True
    soma_type: Final = "SOMASparseNDArray"
