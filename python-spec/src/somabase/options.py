"""Enums and other types used as options across methods of many types.

These types are *concrete* and should be used as-is as inputs to the various
SOMA types that require them, not reimplemented by the implementing package.
"""

from typing import Optional

import attrs


@attrs.define(frozen=True)
class IOfN:
    """Specifies that a read should return partition ``i`` out of ``n`` total.

    For a read operation that returns ``n`` partitions, the read operation will
    return the ``i``th partition (zero-indexed) out of ``n`` partitions of
    approximately equal size.
    """

    i: int = attrs.field()
    """Which partition to return (zero-indexed)."""
    n: int = attrs.field()
    """How many partitions there will be."""

    @i.validator
    def _validate(self, _, __):
        del _, __  # Unused.
        if not 0 <= self.i < self.n:
            raise ValueError(
                f"Partition index {self.i} must be in the range [0, {self.n})"
            )


@attrs.define(frozen=True)
class BatchSize:
    """Specifies the size of a batch that should be returned from reads.

    Read operations on foundational types return an iterator over "batches" of
    data, enabling processing of larger-than-core datasets. This class allows
    you to control what the size of those batches is.

    If none of these options are set, a "reasonable" batch size is determined
    automatically.

    For example::

        BatchSize(count=100)
        # Will return batches of 100 elements.

        BatchSize(bytes=1024 ** 2)
        # Will return batches of up to 1 MB.

        BatchSize()
        # Will return automatically-sized batches.
    """

    count: Optional[int] = attrs.field(default=None)
    """``arrow.Table``s with this number of rows will be returned."""
    bytes: Optional[int] = attrs.field(default=None)
    """Data of up to this size in bytes will be returned."""

    @count.validator
    @bytes.validator
    def _validate(self, attr: attrs.Attribute, value):
        if not value:
            return  # None (or 0, which we treat equivalently) is always valid.
        if value < 0:
            raise ValueError(f"If set, '{attr.name}' must be positive")
        if self.count and self.bytes:
            raise ValueError("Either 'count' or 'bytes' may be set, not both")
