"""Definitions of data storage interfaces for SOMA implementations.

SOMA users should ordinarily not need to import this module directly; relevant
members will be exported to the ``somabase`` namespace.
"""

import abc
from typing import Tuple

import pyarrow
from typing_extensions import Final

from somabase import base


class DataFrame(base.SOMAObject, metaclass=abc.ABCMeta):
    """A multi-column table with a user-defined schema."""

    __slots__ = ()

    # TODO: Read/write.

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

    # TODO: Read/write.

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

    # TODO: Read/write.

    is_sparse: Final = False
    soma_type: Final = "SOMADenseNDArray"


class SparseNDArray(NDArray, metaclass=abc.ABCMeta):
    """A N-dimensional array stored sparsely."""

    __slots__ = ()

    # TODO: Read/write.

    @property
    def nnz(self) -> int:
        """The number of values stored in the array, including explicit zeros.

        For dense arrays, this will be the total size of the array.
        """
        raise NotImplementedError()

    is_sparse: Final = True
    soma_type: Final = "SOMASparseNDArray"
