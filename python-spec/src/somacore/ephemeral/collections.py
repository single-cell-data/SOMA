from typing import Any, Dict, Iterator, NoReturn, Optional, TypeVar

from .. import base
from .. import collection
from .. import experiment
from .. import measurement

_ST = TypeVar("_ST", bound=base.SOMAObject)


class Collection(collection.Collection[_ST]):
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
    def create(cls, *args, **kwargs) -> "Collection":
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


class Measurement(measurement.Measurement, Collection):  # type: ignore[misc]
    """An in-memory Collection with Measurement semantics."""


class Experiment(experiment.Experiment, Collection):  # type: ignore[misc]
    """An in-memory Collection with Experiment semantics."""
