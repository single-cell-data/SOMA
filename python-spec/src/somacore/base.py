"""Definitions of the most fundamental types used by the SOMA project.

SOMA users should ordinarily not need to import this module directly; relevant
members will be exported to the ``somacore`` namespace.
"""

import abc
from typing import Any, ClassVar, MutableMapping, Optional

from typing_extensions import LiteralString, Self

from . import options


class SOMAObject(metaclass=abc.ABCMeta):
    """The base type for all SOMA objects, containing common behaviors."""

    __slots__ = ("__weakref__",)

    @classmethod
    @abc.abstractmethod
    def open(
        cls,
        uri: str,
        mode: options.OpenMode = "r",
        *,
        context: Optional[Any] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> Self:
        """Opens the SOMA object of this type at the given URI.
        [lifecycle: experimental]

        :param uri: The URI of the object to open.
        :param mode: The mode to open this in, either `r` or `w`.
        :param context: The Context value to use when opening the object.
        :param platform_config: Platform configuration options specific to
            this open operation.
        """
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def exists(cls, uri: str, *, context: Optional[Any] = None) -> bool:
        """Checks whether a SOMA object of this type is stored at the URI.

        :param uri: The URI to check.
        :param context: The Context value to use when checking existence.
        :return: True if the object exists and is of the correct type.
            False if the object does not exist, or is of a different type.
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def uri(self) -> str:
        """Returns the URI of this SOMA object. [lifecycle: experimental]"""
        raise NotImplementedError()

    @property
    def context(self) -> Any:
        """A value storing implementation-specific configuration information.
        [lifecycle: experimental]

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
        """The metadata of this SOMA object. [lifecycle: experimental]

        The returned value directly references the stored metadata; reads from
        and writes to it (provided the object is opened) are reflected in
        storage.
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def mode(self) -> options.OpenMode:
        """Returns the mode this object was opened in, either ``r`` or ``w``.
        [lifecycle: experimental]
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def closed(self) -> bool:
        """Returns True if this object has been closed; False if still open.
        [lifecycle: experimental]
        """
        raise NotImplementedError()

    soma_type: ClassVar[LiteralString]
    """A string describing the SOMA type of this object. This is constant."""
    # This uses ClassVar since you can't do abstract class properties.
    # This is the equivalent, just without abc-based automatic verification.
    #
    # Overrides are marked Final with an ignore[misc] because mypy by default
    # wants this to be mutable, and doesn't like overriding the mutable member
    # with a Final member.

    # Context management

    def close(self) -> None:
        """Releases any external resources held by this object.
        [lifecycle: experimental]

        An implementation of close must be idempotent.
        """
        # Default implementation does nothing.

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()
        super_del = getattr(super(), "__del__", lambda: None)
        super_del()

    # Explicitly use Python's identity-based equality/hash checks.
    # These will show up in the `__mro__` before any other classes
    # provided a SOMAObject base is put first:
    #
    #    class SubType(SomeSOMAObject, MutableMapping):
    #        ...
    #
    #    # sub_type_inst.__eq__ uses object.__eq__ rather than
    #    # MutableMapping.__eq__.

    __eq__ = object.__eq__
    __hash__ = object.__hash__
