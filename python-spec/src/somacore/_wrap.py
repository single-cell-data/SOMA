from typing import (
    Any,
    Generic,
    ItemsView,
    Iterator,
    KeysView,
    MutableMapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    ValuesView,
    overload,
)

import attrs
from typing_extensions import Final

from somacore import base

_ST = TypeVar("_ST", bound=base.SOMAObject)
_T = TypeVar("_T")

_SENTINEL = object()


class CollectionProxy(base.Collection[_ST]):
    """Base class to forward SOMA collection methods to a "real" SOMA object.

    This is intended for use as a mixin for SOMA objects that decorate standard
    collection types with behaviors, e.g. the Experiment or Measurement classes.
    It allows the separation of the behaviors (implemented in the decorator)
    from the backend implementation (implemented in the wrapped object).
    """

    __slots__ = ("_backing",)

    def __init__(self, backing: base.Collection[_ST]):
        """Creates a new CollectionProxy backed by the given collection."""
        self._backing: Final = backing
        """The object that actually provides the indexing for this object."""

    # SOMA methods

    @property
    def metadata(self) -> MutableMapping[str, str]:
        return self._backing.metadata

    def unwrap(self) -> base.Collection[_ST]:
        """Unwrap gets the actual collection backed by this proxy."""
        inst: base.Collection[_ST] = self
        while isinstance(inst, CollectionProxy):
            inst = inst._backing
        return inst

    # Sized

    def __len__(self) -> int:
        return len(self._backing)

    # Iterable

    def __iter__(self) -> Iterator[str]:
        return iter(self._backing)

    # Container

    def __contains__(self, key: Any) -> bool:
        return key in self._backing

    # Mapping

    def __getitem__(self, key: str) -> _ST:
        return self._backing[key]

    @overload
    def get(self, key: str) -> Optional[_ST]:
        ...

    @overload
    def get(self, key: str, default: _T) -> Union[_ST, _T]:
        ...

    def get(
        self, key: str, default: Union[_ST, _T, None] = None
    ) -> Union[_ST, _T, None]:
        return self._backing.get(key, default)

    def keys(self) -> KeysView[str]:
        return self._backing.keys()

    def items(self) -> ItemsView[str, _ST]:
        return self._backing.items()

    def values(self) -> ValuesView[_ST]:
        return self._backing.values()

    # __reversed__ is not supported.

    # MutableMapping

    def __setitem__(self, key: str, value: _ST) -> None:
        self._backing[key] = value

    def __delitem__(self, key: str) -> None:
        del self._backing[key]

    def pop(
        self,
        key: str,
        value: Union[_T, _ST] = _SENTINEL,  # type: ignore[assignment]
    ) -> Union[_T, _ST]:
        if value is _SENTINEL:
            return self._backing.pop(key)
        return self._backing.pop(key, value)

    def popitem(self) -> Tuple[str, _ST]:
        return self._backing.popitem()

    def clear(self) -> None:
        self._backing.clear()

    def update(self, __other=(), **kwds) -> None:
        return self._backing.update(__other, **kwds)

    def setdefault(
        self,
        key: str,
        default: _ST = None,  # type: ignore[assignment]
    ) -> _ST:
        return self._backing.setdefault(key, default)  # type: ignore[arg-type]


@attrs.define()
class item(Generic[_T]):
    """Descriptor to transform property access into indexing.

    This descriptor works with :class:`CollectionProxy` to allow for simple
    specification of properties that reflect the members of the collection::

        class WrapImpl(CollectionProxy):

            first = item(str)
            second = item(int, "2nd")

        inst = WrapImpl(some_collection)

        # This is equivalent to getting some_collection["first"]
        inst.first

        # This is equivalent to setting some_collection["2nd"]
        inst.second = 500
    """

    typ: Optional[Type[_T]] = None
    """The type we expect to return from this field."""

    item_name: Optional[str] = None
    """The name of the item we are getting (``x._backing["whatever"]``).

    This uses the name of the field by default but can be manually overridden.
    """

    field_name: str = attrs.field(default="<unknown>", init=False)
    """The name of this field (``x.whatever``). Set automatically."""

    def __set_name__(self, owner: Type[CollectionProxy], name: str) -> None:
        del owner  # unused
        self.field_name = name
        if self.item_name is None:
            self.item_name = name

    @overload
    def __get__(self, inst: None, owner: Type[CollectionProxy]) -> "item[_T]":
        ...

    @overload
    def __get__(self, inst: CollectionProxy, owner: Type[CollectionProxy]) -> _T:
        ...

    def __get__(
        self, inst: Optional[CollectionProxy], owner: Type[CollectionProxy]
    ) -> Union["item", _T]:
        del owner  # unused
        if not inst:
            return self
        assert self.item_name is not None
        try:
            # TODO: Type-check params/returns?
            return inst[self.item_name]
        except KeyError as ke:
            raise AttributeError(
                f"{_typename(inst)!r} object has no attribute {self.field_name!r}"
            ) from ke

    def __set__(self, inst: CollectionProxy, value: _T) -> None:
        assert self.item_name is not None
        # Pretend it's a MutableMapping for the type-checker.
        # If it fails that's OK; we need to raise anyway.
        try:
            inst[self.item_name] = value
        except KeyError as ke:
            raise AttributeError(
                f"{_typename(inst)!r} does not support assigning"
                f" to item {self.item_name!r}"
            ) from ke

    def __delete__(self, inst: CollectionProxy) -> None:
        assert self.item_name is not None
        try:
            del inst[self.item_name]
        except KeyError as ke:
            raise AttributeError(
                f"{_typename(inst)} does not support deleting {self.item_name!r}"
            ) from ke


def _typename(x: object) -> str:
    return type(x).__name__
