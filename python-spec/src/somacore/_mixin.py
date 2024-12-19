"""Tools for making mixins with SOMA Collections."""

from __future__ import annotations

from typing import Generic, MutableMapping, Type, TypeVar, Union, overload

import attrs

from . import base

_ST = TypeVar("_ST", bound=base.SOMAObject)
_Coll = MutableMapping[str, _ST]
_T = TypeVar("_T")


@attrs.define()
class item(Generic[_T]):
    """Descriptor to transform property access into indexing.

    This descriptor works on mapping objects to allow simple specification of
    properties that are backed by map entries::

        class FirstSecondMixin:

            first = item(str)
            second = item(int, "2nd")

        class FSCollection(FirstSecondMixin, CollectionBase):
            pass

        inst = FSCollection(...)

        # This is equivalent to getting inst["first"]
        inst.first

        # This is equivalent to setting inst["2nd"]
        inst.second = 500
    """

    typ: Type[_T] | None = None
    """The type we expect to return from this field."""

    item_name: str | None = None
    """The name of the item we are getting (``x._backing["whatever"]``).

    This uses the name of the field by default but can be manually overridden.
    """

    field_name: str = attrs.field(default="<unknown>", init=False)
    """The name of this field (``x.whatever``). Set automatically."""

    def __set_name__(self, owner: Type[_Coll], name: str) -> None:
        del owner  # unused
        self.field_name = name
        if self.item_name is None:
            self.item_name = name

    @overload
    def __get__(self, inst: None, owner: Type[_Coll]) -> "item[_T]": ...

    @overload
    def __get__(self, inst: _Coll, owner: Type[_Coll]) -> _T: ...

    def __get__(self, inst: _Coll | None, owner: Type[_Coll]) -> Union["item", _T]:
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

    def __set__(self, inst: _Coll, value: _T) -> None:
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

    def __delete__(self, inst: _Coll) -> None:
        assert self.item_name is not None
        try:
            del inst[self.item_name]
        except KeyError as ke:
            raise AttributeError(
                f"{_typename(inst)} does not support deleting {self.item_name!r}"
            ) from ke


def _typename(x: object) -> str:
    return type(x).__name__
