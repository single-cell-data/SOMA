"""Contains a Collection implementation that is only stored in memory."""

from typing import Any, Dict, Iterator, Optional, Type, TypeVar

from typing_extensions import final

from . import base
from . import options

_ST = TypeVar("_ST", bound=base.Collection)


@final
class SimpleCollection(base.Collection[_ST]):
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
