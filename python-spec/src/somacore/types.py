"""Type and interface declarations that are not specific to options."""

from typing import Any, Optional, TypeVar, Sequence
from typing_extensions import Protocol, Self, runtime_checkable, TypeGuard


def is_nonstringy_sequence(it: Any) -> TypeGuard[Sequence]:
    """Returns true if a sequence is a "normal" sequence and not str or bytes.

    str and bytes are "weird" sequences because iterating them gives you
    another str or bytes instance for each character, and when used as a
    sequence is not what users want.
    """
    return not isinstance(it, (str, bytes)) and isinstance(it, Sequence)


class Comparable(Protocol):
    """Objects that can be ``<``/``==``/``>``'d."""

    def __lt__(self, __other: Self) -> bool:
        ...

    def __le__(self, __other: Self) -> bool:
        ...

    def __eq__(self, __other: object) -> bool:
        ...

    def __ne__(self, __other: object) -> bool:
        ...

    def __ge__(self, __other: Self) -> bool:
        ...

    def __gt__(self, __other: Self) -> bool:
        ...


_Cmp_co = TypeVar("_Cmp_co", bound=Comparable, covariant=True)


@runtime_checkable
class Slice(Protocol[_Cmp_co]):
    """A slice which stores a certain type of object.

    This protocol describes the built in ``slice`` type, with a hint to callers
    about what type they should put *inside* the slice.
    """

    @property
    def start(self) -> Optional[_Cmp_co]:
        ...

    @property
    def stop(self) -> Optional[_Cmp_co]:
        ...

    @property
    def step(self) -> Optional[_Cmp_co]:
        ...
