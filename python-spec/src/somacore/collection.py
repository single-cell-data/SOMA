import abc
from typing import Any, Dict, Iterator, MutableMapping, Optional, Type, TypeVar

from typing_extensions import LiteralString, final

from . import base
from . import options

_ST = TypeVar("_ST", bound=base.SOMAObject)
"""Generic type variable for any SOMA object."""


class Collection(base.SOMAObject, MutableMapping[str, _ST], metaclass=abc.ABCMeta):
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
        possible, the collection may construct a new non-relative URI.

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
        """Sets an entry into this collection. See :meth:`set` for details."""
        self.set(key, value)

    @abc.abstractmethod
    def set(
        self, key: str, value: _ST, *, use_relative_uri: Optional[bool] = None
    ) -> None:
        """Sets an entry of this collection.

        Important note: Because parent objects may need to share
        implementation-internal state with children, when you set an item in a
        collection, it is not guaranteed that the SOMAObject instance available
        by accessing the collection is the same as the one that was set::

            some_collection["thing"] = my_soma_object
            added_soma_object = some_collection["thing"]
            my_soma_object is added_soma_object  # could be False

        The two objects *will* refer to the same stored data.

        :param use_relative_uri: Determines whether to store the collection
            entry with a relative URI (provided the storage engine supports it).
            If ``None`` (the default), will automatically determine whether to
            use an absolute or relative URI based on their relative location
            (if supported by the storage engine).
            If ``True``, will always use a relative URI. If the new child does
            not share a relative URI base, or use of relative URIs is not
            possible at all, the collection should throw an exception.
            If ``False``, will always use an absolute URI.
        """
        raise NotImplementedError()

    # This is implemented as a property and not a literal so that it can be
    # overridden with `Final` members in Collection specializations.
    @property
    def soma_type(self) -> LiteralString:
        return "SOMACollection"


@final
class SimpleCollection(Collection[_ST]):
    """A memory-backed SOMA Collection for ad-hoc collection building.

    This Collection implementation exists purely in memory. It can be used to
    build ad-hoc SOMA Collections for one-off analyses, and to combine SOMA
    datasets from different sources that cannot be added to a Collection that
    is represented in storage.

    Entries added to this Collection are not "owned" by the collection; their
    lifecycle is still dictated by the place they were opened from. This
    collection has no ``context`` and ``close``ing it does nothing.
    """

    def __init__(self, *args: Any, **kwargs: _ST):
        """Creates a new Collection.

        Arguments and kwargs are provided as in the ``dict`` constructor.
        """
        self._entries: Dict[str, _ST] = dict(*args, **kwargs)
        self._metadata: Dict[str, Any] = {}

    @property
    def uri(self) -> str:
        return f"somacore:simple-collection:{id(self):x}"

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    def add(
        self,
        key: str,
        cls: Type[_ST],
        *,
        uri: Optional[str] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> _ST:
        del key, cls, uri, platform_config  # All unused
        # TODO: Should we be willing to create Collection-based child elements,
        # like Measurement and Experiment?
        raise TypeError(
            "A SimpleCollection cannot create its own children;"
            " only existing SOMA objects may be added."
        )

    def set(
        self, key: str, value: _ST, *, use_relative_uri: Optional[bool] = None
    ) -> None:
        del use_relative_uri  # Ignored.
        self._entries[key] = value

    def __getitem__(self, key: str) -> _ST:
        return self._entries[key]

    def __delitem__(self, key: str) -> None:
        del self._entries[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
