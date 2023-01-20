"""Definitions of the most fundamental types used by the SOMA project.

SOMA users should ordinarily not need to import this module directly; relevant
members will be exported to the ``somacore`` namespace.
"""

import abc
from typing import Any, MutableMapping, Optional, Type, TypeVar

from typing_extensions import LiteralString

from somacore import options


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


class Collection(SOMAObject, MutableMapping[str, _ST], metaclass=abc.ABCMeta):
    """A generic string-keyed collection of :class:`SOMAObject`s.

    The generic type specifies what type the Collection may contain. At its
    most generic, a Collection may contain any SOMA object, but a subclass
    may specify that it is a Collection of a specific type of SOMA object.
    """

    __slots__ = ()

    @abc.abstractmethod
    def add(
        self,
        key: str,
        cls: Type[_ST],
        *,
        uri: Optional[str] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> _ST:
        """Creates a child member of this collection and adds it.

        This allows the creation of child objects of any type::

            # Create a child Measurement object at the key "density"
            # with default settings.
            #
            # This creates both the backing Measurement collection, as well as
            # the necessary sub-elements to have a complete Measurement.
            density = the_collection.create("density", somacore.Measurement)

            # Create a child DataFrame at the key "data" with a custom URI
            # and additional platform configuration.
            data = the_collection.create(
                "data",
                somacore.DataFrame,
                uri="file:///custom/path/to/df",
                platform_config={"somaimpl": ...},
            )

        By default (in situations where it is possible to do so), the default
        URI used should be a relative URI with its final component as the key.
        For instance, adding sub-element ``data`` to a Collection located at
        ``file:///path/to/coll`` should by default use
        ``file:///path/to/coll/data`` as its URI if possible. If this is not
        possible

        :param key: The key that this child should live at (i.e., it will be
            accessed via ``the_collection[key]``).
        :param cls: The type of child that should be added.
        :param uri: If provided, overrides the default URI that would be used
            to create this object. This may be absolute or relative.
        :param platform_config: Platform-specific configuration options used
            when creating the child.
        """
        raise NotImplementedError()

    def __setitem__(self, key: str, value: _ST) -> None:
        """Sets an entry into this collection.

        Important note: Because parent objects may need to share
        implementation-internal state with children, when you set an item in a
        collection, it is not guaranteed that the SOMAObject instance available
        by accessing the collection is the same as the one that was set::

            some_collection["thing"] = my_soma_object
            added_soma_object = some_collection["thing"]
            my_soma_object is added_soma_object  # could be False

        The two objects *will* refer to the same stored data.
        """
        self.set(key, value)

    @abc.abstractmethod
    def set(
        self, key: str, value: _ST, *, use_relative_uri: Optional[bool] = None
    ) -> None:
        """Sets an entry of this collection.

        :param use_relative_uri: Determines whether to store the collection
            entry with a relative URI (provided the storage engine supports it).
            If ``None`` (the default), will automatically determine whether to
            use an absolute or relative URI based on their relative location
            (if supported by the storage engine).
            If ``True``, will always use a relative URI.
            If ``False``, will always use an absolute URI.
        """
        raise NotImplementedError()

    # This is implemented as a property and not a literal so that it can be
    # overridden with `Final` members in Collection specializations.
    @property
    def soma_type(self) -> LiteralString:
        return "SOMACollection"
