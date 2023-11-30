from typing import Any, Tuple

import attrs
import numpy as np
import pytest
from pytest import mark

import somacore
from somacore import options
from somacore.query import query


@mark.parametrize(
    ["coords", "want"],
    [
        ((), ()),
        ((slice(1, 10),), (slice(1, 10),)),
        ([0, 1, 2], (0, 1, 2)),
        ([1, 1.5, 2], (1, 1.5, 2)),
        ((slice(None), [0, 88, 1001]), (slice(None), (0, 88, 1001))),
        ((slice(2.5, 3.5),), (slice(2.5, 3.5),)),
        (
            (slice(np.datetime64(946684802, "s"), np.datetime64(946684803, "s")),),
            (slice(np.datetime64(946684802, "s"), np.datetime64(946684803, "s")),),
        ),
        (("string-coord", [b"lo", b"hi"]), ("string-coord", (b"lo", b"hi"))),
        ((slice(4, 5), True, None), (slice(4, 5), True, None)),
    ],
)
def test_canonicalization(coords: Any, want: Tuple[options.SparseDFCoord, ...]) -> None:
    axq = somacore.AxisQuery(coords=coords)
    assert want == axq.coords


def test_canonicalization_nparray() -> None:
    axq = somacore.AxisQuery(coords=(1, np.array([1, 2, 3])))

    one, arr = axq.coords
    assert one == 1
    assert (np.array([1, 2, 3]) == arr).all()


@mark.parametrize(
    ["coords"],
    [
        ("forbid bare strings",),
        (b"forbid bare byteses",),
        (999,),
    ],
)
def test_canonicalization_bad(coords) -> None:
    with pytest.raises(TypeError):
        somacore.AxisQuery(coords=coords)


@attrs.define(frozen=True)
class IHaveObsVarStuff:
    obs: int
    var: int
    the_obs_suf: str
    the_var_suf: str


def test_axis_helpers() -> None:
    thing = IHaveObsVarStuff(obs=1, var=2, the_obs_suf="observe", the_var_suf="vary")
    assert 1 == query._Axis.OBS.getattr_from(thing)
    assert 2 == query._Axis.VAR.getattr_from(thing)
    assert "observe" == query._Axis.OBS.getattr_from(thing, pre="the_", suf="_suf")
    assert "vary" == query._Axis.VAR.getattr_from(thing, pre="the_", suf="_suf")
    ovdict = {"obs": "erve", "var": "y", "i_obscure": "hide", "i_varcure": "???"}
    assert "erve" == query._Axis.OBS.getitem_from(ovdict)
    assert "y" == query._Axis.VAR.getitem_from(ovdict)
    assert "hide" == query._Axis.OBS.getitem_from(ovdict, pre="i_", suf="cure")
    assert "???" == query._Axis.VAR.getitem_from(ovdict, pre="i_", suf="cure")
