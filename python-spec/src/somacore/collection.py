import abc
from typing import (
    Any,
    Dict,
    Iterator,
    MutableMapping,
    NoReturn,
    Optional,
    Sequence,
    Type,
    TypeVar,
)

import pyarrow as pa

from . import base
from . import data
from . import options

_ST = TypeVar("_ST", bound=base.SOMAObject)
"""Generic type variable for any SOMA object."""
_CT = TypeVar("_CT", bound="Collection")
"""Any implementation of a Collection."""


class Collection(base.SOMAObject, MutableMapping[str, _ST], metaclass=abc.ABCMeta):
    """A generic string-keyed collection of :class:`SOMAObject`s.

    The generic type specifies what type the Collection may contain. At its
    most generic, a Collection may contain any SOMA object, but a subclass
    may specify that it is a Collection of a specific type of SOMA object.
    """

    __slots__ = ()
    soma_type = "SOMACollection"

    @classmethod
    @abc.abstractmethod
    def create(
        cls: Type[_CT],
        uri: str,
        *,
        platform_config: Optional[options.PlatformConfig] = None,
        context: Optional[Any] = None,
    ) -> _CT:
        """Creates a new Collection at the given URI and returns it.

        The collection will be returned in the opened state.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def add_new_collection(
        self,
        key: str,
        cls: Optional[Type[_CT]] = None,
        *,
        uri: Optional[str] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> _CT:
        """Creates a new sub-collection of this collection.

        To add an existing collection as a sub-element of this collection,
        use :meth:`set` or indexed access instead.

        The type provided is used to create the skeleton of this collection
        as in :meth:`create`. By default, this will create a basic collection::

            # Create a child Measurement object at the key "density"
            # with default settings.
            #
            # This creates both the backing Measurement collection, as well as
            # the necessary sub-elements to have a complete Measurement.
            density = the_collection.add_new_collection("density", somacore.Measurement)

            # This will create a basic Collection as a child.
            sub_child = density.add_new_collection("sub_child")

        In situations where relative URIs are supported, the default URI of the
        child should be a sub-path of the parent URI. The final component
        should be a path-sanitized version of the new key. For instance, adding
        sub-element ``data`` to a Collection located at ``file:///path/to/coll``
        would have a default path of ``file:///path/to/coll/data``. For
        non–URI-safe keys, no specific path-sanitization method is required,
        but as an example, a child named ``non/path?safe`` could use
        ``file:///path/to/coll/non_path_safe`` as its full URI.

        When a specific child URI is specified, that exact URI should be used
        (whether relative or absolute).

        :param key: The key that this child should live at (i.e., it will be
            accessed via ``the_collection[key]``).
        :param cls: The type of child that should be added.
        :param uri: If provided, overrides the default URI that would be used
            to create this object. This may be absolute or relative.
        :param platform_config: Platform-specific configuration options used
            when creating the child.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def add_new_dataframe(
        self,
        key: str,
        *,
        uri: Optional[str] = None,
        schema: pa.Schema,
        index_column_names: Sequence[str] = (options.SOMA_JOINID,),
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> data.DataFrame:
        """Creates a new DataFrame as a child of this collection.

        Parameters are as in :meth:`data.DataFrame.create`.
        See :meth:`add_new_collection` for details about child creation.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def add_new_dense_ndarray(
        self,
        key: str,
        *,
        uri: Optional[str] = None,
        type: pa.DataType,
        shape: Sequence[int],
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> data.DenseNDArray:
        """Creates a new dense NDArray as a child of this collection.

        Parameters are as in :meth:`data.DenseNDArray.create`.
        See :meth:`add_new_collection` for details about child creation.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def add_new_sparse_ndarray(
        self,
        key: str,
        *,
        uri: Optional[str] = None,
        type: pa.DataType,
        shape: Sequence[int],
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> data.SparseNDArray:
        """Creates a new sparse NDArray as a child of this collection.

        Parameters are as in :meth:`data.SparseNDArray.create`.
        See :meth:`add_new_collection` for details about child creation.
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

    @classmethod
    def open(cls, *args, **kwargs) -> NoReturn:
        del args, kwargs  # All unused
        raise TypeError("SimpleCollections are in-memory only and cannot be opened.")

    @classmethod
    def create(cls, *args, **kwargs) -> "SimpleCollection":
        del args, kwargs  # All unused
        # SimpleCollection is in-memory only, so just return a new empty one.
        return cls()

    def add_new_collection(self, *args, **kwargs) -> NoReturn:
        del args, kwargs  # All unused
        # TODO: Should we be willing to create Collection-based child elements,
        # like Measurement and Experiment?
        raise TypeError(
            "A SimpleCollection cannot create its own children;"
            " only existing SOMA objects may be added."
        )

    add_new_dataframe = add_new_collection
    add_new_sparse_ndarray = add_new_collection
    add_new_dense_ndarray = add_new_collection

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
