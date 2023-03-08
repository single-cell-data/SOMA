"""Type and interface declarations that are not specific to options.

These declarations and functions are not directly part of the user-facing API,
but are intended to be used by SOMA implementations for annotations and
their own internal type-checking purposes.
"""

import sys
from typing import TYPE_CHECKING, NoReturn, Optional, Sequence, Type, TypeVar

from typing_extensions import Protocol, TypeGuard


def is_nonstringy_sequence(it: object) -> TypeGuard[Sequence]:
    """Returns true if a sequence is a "normal" sequence and not str or bytes.

    str and bytes are "weird" sequences because iterating them gives you
    another str or bytes instance for each character, and when used as a
    sequence is not what users want.
    """
    return not isinstance(it, (str, bytes)) and isinstance(it, Sequence)


_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)


class Slice(Protocol[_T_co]):
    """A slice which stores a certain type of object.

    This protocol describes the built in ``slice`` type, with a hint to callers
    about what type they should put *inside* the slice.  It is for type
    annotations only and is not runtime-checkable (i.e., you can't do
    ``isinstance(thing, Slice)``), because ``range`` objects also have
    ``start``/``stop``/``step`` and would match, but are *not* slices.
    """

    @property
    def start(self) -> Optional[_T_co]:
        ...

    @property
    def stop(self) -> Optional[_T_co]:
        ...

    @property
    def step(self) -> Optional[_T_co]:
        ...

    if sys.version_info < (3, 10) and not TYPE_CHECKING:
        # Python 3.9 and below have a bug where any Protocol with an @property
        # was always regarded as runtime-checkable.
        @classmethod
        def __subclasscheck__(cls, __subclass: type) -> NoReturn:
            raise TypeError("Slice is not a runtime-checkable protocol")


def is_slice_of(__obj: object, __typ: Type[_T]) -> TypeGuard[Slice[_T]]:
    return (
        # We only respect `slice`s proper.
        isinstance(__obj, slice)
        and (__obj.start is None or isinstance(__obj.start, __typ))
        and (__obj.stop is None or isinstance(__obj.stop, __typ))
        and (__obj.step is None or isinstance(__obj.step, __typ))
    )
