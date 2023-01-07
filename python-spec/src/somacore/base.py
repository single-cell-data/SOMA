"""Definitions of the most fundamental types used by the SOMA project.

SOMA users should ordinarily not need to import this module directly; relevant
members will be exported to the ``somacore`` namespace.
"""

import abc
from typing import Any, MutableMapping, TypeVar

from typing_extensions import LiteralString


class SOMAObject(metaclass=abc.ABCMeta):
    """A sentinel interface indicating that this type is a SOMA object."""

    __slots__ = ("__weakref__",)

    @property
    def context(self) -> Any:
        """A value storing implementation-specific configuration information.

        This contains long-lived (i.e., not call-specific) information that is
        used by the SOMA implementation to access storage. This may include
        things like credentials, endpoint locations, or database connections.

        End users should treat this as an opaque value. While it may be passed
        from an existing SOMA object to be used in the creation of a new SOMA
        object, it should not be inspected.
        """
        return None

    @property
    @abc.abstractmethod
    def metadata(self) -> MutableMapping[str, Any]:
        """The metadata of this SOMA object.

        The returned value directly references the stored metadata; reads from
        and writes to it (provided the object is opened) are reflected in
        storage.
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def soma_type(self) -> LiteralString:
        """A string describing the SOMA type of this object."""
        raise NotImplementedError()


_ST = TypeVar("_ST", bound=SOMAObject)
"""Generic type variable for any SOMA object."""


class Collection(SOMAObject, MutableMapping[str, _ST]):
    """A generic string-keyed collection of :class:`SOMAObject`s.

    The generic type specifies what type the Collection may contain. At its
    most generic, a Collection may contain any SOMA object, but a subclass
    may specify that it is a Collection of a specific type of SOMA object.
    """

    __slots__ = ()

    # This is implemented as a property and not a literal so that it can be
    # overridden with `Final` members in Collection specializations.
    @property
    def soma_type(self) -> LiteralString:
        return "SOMACollection"
