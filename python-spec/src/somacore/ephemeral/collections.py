from typing import Any, Dict, Iterator, NoReturn, Optional, TypeVar

from typing_extensions import Literal, Self

from .. import base
from .. import collection
from .. import data
from .. import experiment
from .. import measurement
from .. import options

_Elem = TypeVar("_Elem", bound=base.SOMAObject)


class BaseCollection(collection.BaseCollection[_Elem]):
    """A memory-backed SOMA Collection for ad-hoc collection building.

    This Collection implementation exists purely in memory. It can be used to
    build ad-hoc SOMA Collections for one-off analyses, and to combine SOMA
    datasets from different sources that cannot be added to a Collection that
    is represented in storage.

    Entries added to this Collection are not "owned" by the collection; their
    lifecycle is still dictated by the place they were opened from. This
    collection has no ``context`` and ``close``ing it does nothing.
    """

    __slots__ = ("_entries", "_metadata")

    def __init__(self, *args: Any, **kwargs: _Elem):
        """Creates a new Collection.

        Arguments and kwargs are provided as in the ``dict`` constructor.
        """
        self._entries: Dict[str, _Elem] = dict(*args, **kwargs)
        self._metadata: Dict[str, Any] = {}

    @property
    def uri(self) -> str:
        return f"somacore:ephemeral-collection:{id(self):x}"

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    @classmethod
    def open(cls, *args, **kwargs) -> NoReturn:
        del args, kwargs  # All unused
        raise TypeError(
            "Ephemeral collections are in-memory only and cannot be opened."
        )

    @classmethod
    def exists(cls, uri: str, *, context: Any = None) -> Literal[False]:
        del uri, context  # All unused.
        # Ephemeral collections are in-memory only and do not otherwise exist.
        return False

    @classmethod
    def create(cls, *args, **kwargs) -> Self:
        del args, kwargs  # All unused
        # ThisCollection is in-memory only, so just return a new empty one.
        return cls()

    def add_new_collection(self, *args, **kwargs) -> NoReturn:
        del args, kwargs  # All unused
        # TODO: Should we be willing to create Collection-based child elements,
        # like Measurement and Experiment?
        raise TypeError(
            "An ephemeral Collection cannot create its own children;"
            " only existing SOMA objects may be added."
        )

    add_new_dataframe = add_new_collection
    add_new_sparse_ndarray = add_new_collection
    add_new_dense_ndarray = add_new_collection

    @property
    def closed(self) -> bool:
        return False  # With no backing storage, there is nothing to close.

    @property
    def mode(self) -> options.OpenMode:
        return "w"  # This collection is always writable.

    def set(
        self, key: str, value: _Elem, *, use_relative_uri: Optional[bool] = None
    ) -> Self:
        del use_relative_uri  # Ignored.
        self._entries[key] = value
        return self

    def __getitem__(self, key: str) -> _Elem:
        return self._entries[key]

    def __delitem__(self, key: str) -> None:
        del self._entries[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)


class Collection(BaseCollection[_Elem], collection.Collection):
    """An in-memory Collection imposing no semantics on the contents."""

    __slots__ = ()


_BasicAbstractMeasurement = measurement.Measurement[
    data.DataFrame,
    collection.Collection[data.NDArray],
    collection.Collection[data.DenseNDArray],
    collection.Collection[data.SparseNDArray],
    base.SOMAObject,
]
"""The loosest possible constraint of the abstract Measurement type."""


class Measurement(BaseCollection[base.SOMAObject], _BasicAbstractMeasurement):
    """An in-memory Collection with Measurement semantics."""

    __slots__ = ()


class Experiment(
    BaseCollection[base.SOMAObject],
    experiment.Experiment[
        data.DataFrame,
        collection.Collection[_BasicAbstractMeasurement],
        base.SOMAObject,
    ],
):
    """An in-memory Collection with Experiment semantics."""

    __slots__ = ()
