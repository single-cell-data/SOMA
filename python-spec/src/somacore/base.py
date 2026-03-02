"""Definitions of the most fundamental types used by the SOMA project.

SOMA users should ordinarily not need to import this module directly; relevant
members will be exported to the ``somacore`` namespace.
"""

from __future__ import annotations

from typing import Any, MutableMapping, runtime_checkable

from typing_extensions import Protocol, Self

from . import options
from . import types


@runtime_checkable
class SOMAObject(Protocol):
    """The base type for all SOMA objects, containing common behaviors."""

    @classmethod
    def open(
        cls,
        uri: str,
        mode: options.OpenMode = "r",
        *,
        context: Any | None = None,
        platform_config: options.PlatformConfig | None = None,
    ) -> Self:
        """Opens the SOMA object of this type at the given URI.

        Args:
            uri: The URI of the object to open.
            mode: The mode to open this in, either `r` or `w`.
            context: The Context value to use when opening the object.
            platform_config: Platform configuration options specific to
                this open operation.
        Returns: The SOMA object, opened for reading.
        Lifecycle: maturing
        """
        ...

    @classmethod
    def exists(cls, uri: str, *, context: Any | None = None) -> bool:
        """Checks whether a SOMA object of this type is stored at the URI.

        Args:
            uri: The URI to check.
            context: The Context value to use when checking existence.
        Returns:
            True if the object exists and is of the correct type.
            False if the object does not exist, or is of a different type.
        Lifecycle: maturing
        """
        ...

    @property
    def uri(self) -> str:
        """The URI of this SOMA object.

        Lifecycle: maturing
        """
        ...

    @property
    def context(self) -> types.ContextBase | None:
        """A value storing implementation-specific configuration information.

        This contains long-lived (i.e., not call-specific) information that is
        used by the SOMA implementation to access storage. This may include
        things like credentials, endpoint locations, or database connections.

        End users should treat this as an opaque value. While it may be passed
        from an existing SOMA object to be used in the creation of a new SOMA
        object, it should not be inspected.

        Lifecycle: maturing
        """
        ...

    @property
    def metadata(self) -> MutableMapping[str, Any]:
        """The metadata of this SOMA object.

        The returned value directly references the stored metadata; reads from
        and writes to it (provided the object is opened) are reflected in
        storage.

        Lifecycle: maturing
        """
        ...

    @property
    def mode(self) -> options.OpenMode:
        """Returns the mode this object was opened in, either ``r`` or ``w``.

        Lifecycle: maturing
        """
        ...

    @property
    def closed(self) -> bool:
        """True if this object has been closed; False if still open.

        Lifecycle: maturing
        """
        ...

    # Context management

    def close(self) -> None:
        """Releases any external resources held by this object.

        For objects opened for write, this also finalizes the write operation
        and ensures that all writes are completed before returning.

        This is also called automatically by the Python interpreter via
        ``__del__`` when this object is garbage collected, so the implementation
        must be idempotent.

        Lifecycle: maturing
        """
        ...

    def __enter__(self) -> Self: ...

    def __exit__(self, *_: Any) -> None: ...
