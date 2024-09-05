"""Implementation of the SOMA scene collection for spatial data"""

import abc
from typing import Generic, Optional, TypeVar, Union

from typing_extensions import Final

from . import _mixin
from . import base
from . import collection
from . import coordinates
from . import spatialdata

_ImageColl = TypeVar("_ImageColl", bound=spatialdata.MultiscaleImage)
"""A particular implementation of a collection of spatial arrays."""
_SpatialDFColl = TypeVar(
    "_SpatialDFColl",
    bound=collection.Collection[
        Union[spatialdata.PointCloud, spatialdata.GeometryDataFrame]
    ],
)
_NestedSpatialDFColl = TypeVar(
    "_NestedSpatialDFColl",
    bound=collection.Collection[
        collection.Collection[
            Union[spatialdata.PointCloud, spatialdata.GeometryDataFrame]
        ]
    ],
)
_RootSO = TypeVar("_RootSO", bound=base.SOMAObject)
"""The root SomaObject type of the implementation."""


class Scene(
    collection.BaseCollection[_RootSO],
    Generic[_ImageColl, _SpatialDFColl, _NestedSpatialDFColl, _RootSO],
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
    #             ImplMultiscaleImage,
    #             ImplCollection[
    #                 Union[ImplGeometryDataFrame, ImplPointCloud]]
    #             ], # _SpatialDFColl
    #             ImplCollection[
    #                 ImplCollection[
    #                     Union[ImplGeometryDataFrame, ImplPointCloud]]
    #                 ]
    #             ], # _SpatialDFColl
    #             ImplSOMAObject,
    #         ],
    #     ):
    #         ...

    __slots__ = ()
    soma_type: Final = "SOMAScene"  # type: ignore[misc]

    img = _mixin.item[_ImageColl]()
    """A collection of multi-scale imagery backing the spatial data."""

    obsl = _mixin.item[_SpatialDFColl]()
    """A dataframe of the obs locations

    This collection exists to store any spatial data in the scene that joins on the obs
    ``soma_joinid``.

    Each dataframe in ``obsl`` can be either a GeometryDataFrame or a PointCloud. It
    must contain a ``soma_joinid`` and at least 2 spatial dimensions (naming
    convention for spatial dimensions TBD). If it is a ``GeometryDataFrame`` it must
    contain a ``soma_geometry`` column that is either (1) a number type for a
    collection of only circles or (2) a WKB blob for arbitrary 2D geometries. Other
    additional columns may be stored in this dataframe as well.
     """

    varl = _mixin.item[_NestedSpatialDFColl]()
    """A collection of collections of dataframes of the var locations.

    This collection exists to store any spatial data in the scene that joins on the
    var ``soma_joinid``. The top-level collection maps from measurement name to a
    collection of dataframes.

    Each dataframe in ``varl`` can be either a GeometryDataFrame or a PointCloud. It
    must contain a ``soma_joinid`` and at least 2 spatial dimensions (naming
    convention for spatial dimensions TBD). If it is a ``GeometryDataFrame`` it must
    contain a ``soma_geometry`` column that is either (1) a number type for a
    collection of only circles or (2) a WKB blob for arbitrary 2D geometries. Other
    additional columns may be stored in this dataframe as well.
    """

    @property
    @abc.abstractmethod
    def coordinate_space(self) -> Optional[coordinates.CoordinateSpace]:
        """Coordinate system for this scene."""
        raise NotImplementedError()
