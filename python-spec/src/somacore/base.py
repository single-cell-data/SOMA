"""Definitions of the most fundamental types used by the SOMA project.

SOMA users should ordinarily not need to import this module directly; relevant
members will be exported to the ``somacore`` namespace.
"""

import abc
from typing import Any, MutableMapping, Optional, Type, TypeVar

from typing_extensions import LiteralString

from . import options

_ST = TypeVar("_ST", bound="SOMAObject")


class SOMAObject(metaclass=abc.ABCMeta):
    """A sentinel interface indicating that this type is a SOMA object."""

    __slots__ = ("__weakref__",)

    @classmethod
    @abc.abstractmethod
    def open(
        cls: Type[_ST],
        uri: str,
        mode: options.OpenMode = "r",
        *,
        context: Optional[Any] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> _ST:
        """Opens the SOMA object at the given URL."""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def uri(self) -> str:
        """Returns the URI of this SOMA object."""
        raise NotImplementedError()

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

    # Context management

    def close(self) -> None:
        """Releases any external resources held by this object.

        An implementation of close must be idempotent.
        """
        # Default implementation does nothing.

    def __enter__(self: _ST) -> _ST:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()
        super_del = getattr(super(), "__del__", lambda: None)
        super_del()
