"""Implementation of the SOMA scene collection for spatial data"""

from typing import Generic, TypeVar, Union

from typing_extensions import Final

from . import _mixin
from . import base
from . import collection
from . import data

_DF = TypeVar("_DF", bound=data.DataFrame)
"""A particular implementation of DataFrame."""
_SpatialColl = TypeVar(
    "_SpatialColl", bound=collection.Collection[Union[data.DataFrame, data.NDArray]]
)
"""A particular implementation of a collection of spatial arrays."""
_RootSO = TypeVar("_RootSO", bound=base.SOMAObject)
"""The root SomaObject type of the implementation."""


class Scene(
    collection.BaseCollection[_RootSO],
    Generic[_SpatialColl, _RootSO],
):
    """TODO: Add documentation for scene

    Lifecycle: experimental
    """

    # This class is implemented as a mixin to be used with SOMA classes.
    # For example, a SOMA implementation would look like this:
    #
    #     # This type-ignore comment will always be needed due to limitations
    #     # of type annotations; it is (currently) expected.
    #     class Scene(  # type: ignore[type-var]
    #         ImplBaseCollection[ImplSOMAObject],
    #         somacore.Scene[
    #             ImplCollection[Union[ImplDF, ImplNDArray]],  # _SpatialColl
    #             ImplSOMAObject,                              # _RootSO
    #         ],
    #     ):
    #         ...

    __slots__ = ()
    soma_type: Final = "SOMAScene"  # type: ignore[misc]

    obsl = _mixin.item[_SpatialColl]()
    """A collection of spatial data defined on the obs data"""

    varl = _mixin.item[collection.Collection[_SpatialColl]]()
    """A collection of collections of spatial data defined on a measurement variable"""
