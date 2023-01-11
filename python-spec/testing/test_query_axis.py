from typing import Tuple

import numpy as np
import pytest
from pytest import mark

from somacore import options
from somacore.query import axis


@mark.parametrize(
    ["coords", "want"],
    [
        ((slice(1, 10),), (slice(1, 10),)),
        ([0, 1, 2], (0, 1, 2)),
        ((slice(None), [0, 88, 1001]), (slice(None), (0, 88, 1001))),
        pytest.param(
            ("string-coord",),
            ("string-coord",),
            marks=mark.xfail(reason="strings not supported yet"),
        ),
        pytest.param(
            (b"bytes-coord",),
            (b"bytes-coord",),
            marks=mark.xfail(reason="bytes not supported yet"),
        ),
    ],
)
def test_canonicalization(
    coords: options.SparseDFCoords, want: Tuple[options.SparseDFCoord, ...]
) -> None:
    axq = axis.AxisQuery(coords=coords)
    assert want == axq.coords


def test_canonicalization_nparray() -> None:
    axq = axis.AxisQuery(coords=(1, np.array([1, 2, 3])))

    one, arr = axq.coords
    assert one == 1
    assert (np.array([1, 2, 3]) == arr).all()


@mark.parametrize(
    ["coords"],
    [
        ("forbid bare strings",),
        (b"forbid bare byteses",),
        ([1, 1.5, 2],),
    ],
)
def test_canonicalization_bad(coords) -> None:
    with pytest.raises(TypeError):
        axis.AxisQuery(coords=coords)
