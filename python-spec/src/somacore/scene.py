"""Implementation of the SOMA scene collection for spatial data"""

from typing import Generic, TypeVar

from typing_extensions import Final

from . import _mixin
from . import base
from . import collection
from . import data

_SpatialDF = TypeVar("_SpatialDF", bound=data.DataFrame)
"""A particular implementation of GeometryDataFrame and PointCloud."""
_ImageColl = TypeVar("_ImageColl", bound=collection.Collection[data.NDArray])
"""A particular implementation of a collection of spatial arrays."""
_RootSO = TypeVar("_RootSO", bound=base.SOMAObject)
"""The root SomaObject type of the implementation."""


class Scene(
    collection.BaseCollection[_RootSO],
    Generic[_SpatialDF, _ImageColl, _RootSO],
):
    """A set of spatial data defined on a single physical coordinate system.

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

    img = _mixin.item[collection.Collection[_ImageColl]]()
    """A collection of imagery of the spatial data in the scene

    Each collection in this collection may contain either a single image or a
    multi-resolution collection of images.

    Lifecycle: experimental
    """

    obsl = _mixin.item[collection.Collection[_SpatialDF]]()
    """A dataframe of the obs locations

    This collection stores any spatial data in the scene that joins on the observables
    in the parent ``Experiment``'s ``obs`` dataframe. The ``soma_joinid`` for
    dataframes in this collection join on the ``obsid``.

    Lifecycle: experimental
    """

    varl = _mixin.item[collection.Collection[collection.Collection[_SpatialDF]]]()
    """A collection of collections of dataframes of the var locations.

    This collection stores any spatial data in the scene that joins on the annoted
    variables stored in the ``Measurement``'s ``var`` dataframes in the parent
    ``Experiment``.

    The top-level collection maps from measurement name to a collection of dataframes.
    The ``soma_joinid`` of dataframes inside each of these collections join on the
    ``varid`` of the respective ``Measuremetn``.

    Lifecycle: experimental
    """
