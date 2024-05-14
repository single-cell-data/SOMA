"""Implementation of the SOMA scene collection for spatial data"""

from typing import Generic, TypeVar

from typing_extensions import Final

from . import _mixin
from . import base
from . import collection
from . import data

_SpatialDF = TypeVar(
    "_SpatialDF", bound=data.DataFrame
)  # TODO: Update to GeometryDataFrame or PointCloud
"""A particular implementation of GeometryDataFrame and PointCloud."""
_ImageColl = TypeVar(
    "_ImageColl", bound=collection.Collection[data.NDArray]
)  # TODO: Update to be SpatialArray or ImageArray or ImageCollection (tdb)
"""A particular implementation of a collection of spatial arrays."""
_RootSO = TypeVar("_RootSO", bound=base.SOMAObject)
"""The root SomaObject type of the implementation."""


class Scene(
    collection.BaseCollection[_RootSO],
    Generic[_SpatialDF, _ImageColl, _RootSO],
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
    #             Union[ImplGeometryDataFrame, ImplPointCloud], # _SpatialDF
    #             ImplImageCollection,                          # _ImageColl
    #             ImplSOMAObject,                               # _RootSO
    #         ],
    #     ):
    #         ...

    __slots__ = ()
    soma_type: Final = "SOMAScene"  # type: ignore[misc]

    img = _mixin.item[_ImageColl]()
    """A collection of imagery backing the spatial data"""

    obsl = _mixin.item[_SpatialDF]()
    """A dataframe of the obs locations"""

    varl = _mixin.item[collection.Collection[_SpatialDF]]()
    """A collection of dataframes of the var locations"""

    obssm = _mixin.item[_SpatialDF]()  # TODO: Discuss name
    """Spatial metadata annotations of obs"""

    varsm = _mixin.item[_SpatialDF]()  # TODO: Discuss name
    """Spatial metadata annotations of var"""
