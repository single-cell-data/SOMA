"""The most fundamental types used by the SOMA project."""

from typing import MutableMapping, TypeVar


class SOMAObject:
    """A sentinel interface indicating that this type is a SOMA object."""

    __slots__ = ()

    # TODO: Consider if there are any more fundamental behaviors that should be
    # pushed down to the SOMAObject level.


_ST = TypeVar("_ST", bound=SOMAObject)
"""Generic type variable for any SOMA object."""


class Collection(SOMAObject, MutableMapping[str, _ST]):
    """A generic string-keyed collection of :class:`SOMAObject`s.

    The generic type specifies what type the Collection may contain. At its
    most generic, a Collection may contain any SOMA object, but a subclass
    may specify that it is a Collection of a specific type of SOMA object.
    """

    __slots__ = ()
