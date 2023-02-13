import abc
from typing import Any, MutableMapping, Optional, Sequence, Type, TypeVar, overload

import pyarrow as pa
from typing_extensions import Final, Self

from . import base
from . import data
from . import options

_Elem = TypeVar("_Elem", bound=base.SOMAObject)
"""Element Type for a SOMA collection."""
_CT = TypeVar("_CT", bound="BaseCollection")
"""Any implementation of a Collection."""


class BaseCollection(
    base.SOMAObject, MutableMapping[str, _Elem], metaclass=abc.ABCMeta
):
    """A generic string-keyed collection of :class:`SOMAObject`s.
    [lifecycle: experimental]

    The generic type specifies what type the Collection may contain. At its
    most generic, a Collection may contain any SOMA object, but a subclass
    may specify that it is a Collection of a specific type of SOMA object.
    """

    __slots__ = ()

    @classmethod
    @abc.abstractmethod
    def create(
        cls,
        uri: str,
        *,
        platform_config: Optional[options.PlatformConfig] = None,
        context: Optional[Any] = None,
    ) -> Self:
        """Creates a new collection of this type at the given URI.
        [lifecycle: experimental]

        The collection will be returned opened for writing.
        """
        raise NotImplementedError()

    # Overloads to allow type inference to work when doing:
    #
    #     some_coll.add_new_collection("key")  # -> Collection
    # and
    #     some_coll.add_new_collection("key", Experiment)  # -> Experiment

    @overload
    @abc.abstractmethod
    def add_new_collection(
        self,
        key: str,
        cls: None = None,
        *,
        uri: Optional[str] = ...,
        platform_config: Optional[options.PlatformConfig] = ...,
    ) -> "Collection":
        ...

    @overload
    @abc.abstractmethod
    def add_new_collection(
        self,
        key: str,
        cls: Type[_CT],
        *,
        uri: Optional[str] = ...,
        platform_config: Optional[options.PlatformConfig] = ...,
    ) -> _CT:
        ...

    @abc.abstractmethod
    def add_new_collection(
        self,
        key: str,
        cls: Optional[Type["BaseCollection"]] = None,
        *,
        uri: Optional[str] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> "BaseCollection":
        """Creates a new sub-collection of this collection.
        [lifecycle: experimental]

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
        [lifecycle: experimental]

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
        [lifecycle: experimental]

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
        [lifecycle: experimental]

        Parameters are as in :meth:`data.SparseNDArray.create`.
        See :meth:`add_new_collection` for details about child creation.
        """
        raise NotImplementedError()

    def __setitem__(self, key: str, value: _Elem) -> None:
        """Sets an entry into this collection. See :meth:`set` for details."""
        self.set(key, value)

    @abc.abstractmethod
    def set(
        self, key: str, value: _Elem, *, use_relative_uri: Optional[bool] = None
    ) -> Self:
        """Sets an entry of this collection. [lifecycle: experimental]

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
        :return: ``self``, to enable method chaining.
        """
        raise NotImplementedError()


class Collection(BaseCollection[_Elem]):
    """SOMA Collection imposing no semantics on the contained values.
    [lifecycle: experimental]
    """

    soma_type: Final = "SOMACollection"  # type: ignore[misc]
    __slots__ = ()
