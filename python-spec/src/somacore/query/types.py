"""Common types used across SOMA query modules."""

from typing import Any, Callable

import numpy as np
import numpy.typing as npt
from typing_extensions import Protocol


class IndexLike(Protocol):
    """The basics of what we expect an Index to be.

    This is a basic description of the parts of the ``pandas.Index`` type
    that we use. It is intended as a rough guide so an implementor can know
    that they are probably passing the right "index" type into a function,
    not as a full specification of the types and behavior of ``get_indexer``.
    """

    def get_indexer(
        self,
        target: npt.NDArray[np.int64],
        method: object = ...,
        limit: object = ...,
        tolerance: object = ...,
    ) -> Any:
        """Something compatible with Pandas' Index.get_indexer method."""


IndexFactory = Callable[[npt.NDArray[np.int64]], "IndexLike"]
"""Function that builds an index over the given NDArray.

This interface is implemented by the callable ``pandas.Index``.
"""
