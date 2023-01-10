"""Contains a Collection implementation that is only stored in memory."""

from typing import Any, Dict, Iterator

from typing_extensions import final

from somacore import base


@final
class SimpleCollection(base.Collection):
    """A memory-backed SOMA Collection for ad-hoc collection building.

    This Collection implementation exists purely in memory. It can be used to
    build ad-hoc SOMA Collections for one-off analyses, and to combine SOMA
    datasets from different sources that cannot be added to a Collection that
    is represented in storage.

    Entries added to this Collection are not "owned" by the collection; their
    lifecycle is still dictated by the place they were opened from. This
    collection has no ``context`` and ``close``ing it does nothing.
    """

    def __init__(self, *args: Any, **kwargs: base.SOMAObject):
        """Creates a new Collection.

        Arguments and kwargs are provided as in the ``dict`` constructor.
        """
        self._entries: Dict[str, base.SOMAObject] = dict(*args, **kwargs)
        self._metadata: Dict[str, Any] = {}

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    def __getitem__(self, item: str) -> base.SOMAObject:
        return self._entries[item]

    def __setitem__(self, item: str, value: base.SOMAObject) -> None:
        self._entries[item] = value

    def __delitem__(self, item: str) -> None:
        del self._entries[item]

    def __iter__(self) -> Iterator[str]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
