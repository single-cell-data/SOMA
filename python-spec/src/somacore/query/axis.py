from typing import Optional, Sequence, Tuple

import attrs
import numpy as np
import pyarrow as pa

from .. import options
from .. import types


def _canonicalize_coords(
    in_coords: Optional[options.SparseDFCoords],
) -> Tuple[options.SparseDFCoord, ...]:
    """Validates coordinates and freezes sequences as tuples.

    This is not strictly necessary; DataFrame will report these errors
    eventually but doing it now makes for better UX.
    """
    if in_coords is None:
        return (slice(None),)
    if not isinstance(in_coords, Sequence):
        raise TypeError(
            f"query coordinates must be a sequence, not a single {type(in_coords)}"
        )
    if not types.is_nonstringy_sequence(in_coords):
        raise TypeError(
            "query coordinates must be a normal sequence, not `str` or `bytes`."
        )
    return tuple(_canonicalize_coord(c) for c in in_coords)


def _canonicalize_coord(coord: options.SparseDFCoord) -> options.SparseDFCoord:
    """Validates a single coordinate, freezing mutable sequences."""
    if coord is None or isinstance(
        coord, (bytes, int, slice, str, pa.Array, pa.ChunkedArray, np.ndarray)
    ):
        return coord
    if isinstance(coord, Sequence):
        # We're trusting here that the elements of the user's sequence are
        # appropriate. If this is not the case, it will raise down the line.
        return tuple(coord)
    raise TypeError(f"{type(coord)} object cannot be used as a coordinate.")


@attrs.define(frozen=True, kw_only=True)
class AxisQuery:
    """Single-axis dataframe query with coordinates and a value filter.

    [lifecycle: experimental]
    Per dimension, the AxisQuery can have value of:

    * None - all data
    * Coordinates - a set of coordinates on the axis dataframe index,
      expressed in any type or format supported by ``DataFrame.read()``.
    * A SOMA ``value_filter`` across columns in the axis dataframe,
      expressed as string
    * Or, a combination of coordinates and value filter.

    Examples::

        AxisQuery()  # all data
        AxisQuery(coords=None)  # also all data
        AxisQuery(coords=(slice(1,10),))  # 1D, slice
        AxisQuery(coords=([0,1,2]))  # 1D, point indexing using array-like
        AxisQuery(coords=(slice(None), numpy.array([0,88,1001])))  # 2D
        AxisQuery(value_filter="tissue == 'lung'")
        AxisQuery(coords=(slice(1,None),), value_filter="tissue == 'lung'")
    ```
    """

    value_filter: Optional[str] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )
    """A string specifying a SOMA ``value_filter``."""
    coords: Tuple[options.SparseDFCoord, ...] = attrs.field(
        default=(slice(None),),
        converter=_canonicalize_coords,
    )
    """Query (slice) by dimension.

    The tuple must have a length less than or equal to the number of dimensions,
    and be of a type supported by ``DataFrame``.
    """
