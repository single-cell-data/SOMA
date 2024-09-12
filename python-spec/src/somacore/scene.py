"""Implementation of the SOMA scene collection for spatial data"""

import abc
from typing import Generic, Optional, Sequence, TypeVar, Union

from typing_extensions import Final

from . import _mixin
from . import base
from . import collection
from . import coordinates
from . import spatialdata

_MultiscaleImage = TypeVar("_MultiscaleImage", bound=spatialdata.MultiscaleImage)
"""A particular implementation of a multiscale image."""

_PointCloud = TypeVar("_PointCloud", bound=spatialdata.PointCloud)
"""A particular implementation of a point cloud."""

_GeometryDataFrame = TypeVar("_GeometryDataFrame", bound=spatialdata.GeometryDataFrame)
"""A particular implementation of a geometry dataframe."""

_RootSO = TypeVar("_RootSO", bound=base.SOMAObject)
"""The root SomaObject type of the implementation."""


class Scene(
    collection.BaseCollection[_RootSO],
    Generic[_MultiscaleImage, _PointCloud, _GeometryDataFrame, _RootSO],
):
    """A collection subtype representing spatial assets that can all be stored
    on a single coordinate space.

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
    #             ImplPointCloud,
    #             ImplGeometryDataFrame,
    #             ImplSOMAObject,
    #         ],
    #     ):
    #         ...

    __slots__ = ()
    soma_type: Final = "SOMAScene"  # type: ignore[misc]

    img = _mixin.item[collection.Collection[_MultiscaleImage]]()
    """A collection of multiscale images backing the spatial data."""

    obsl = _mixin.item[collection.Collection[Union[_PointCloud, _GeometryDataFrame]]]()
    """A collection of observation location data.

    This collection exists to store any spatial data in the scene that joins on the obs
    ``soma_joinid``. Each dataframe in ``obsl`` can be either a PointCloud
    or a GeometryDataFrame.
    """

    varl = _mixin.item[
        collection.Collection[
            collection.Collection[Union[_PointCloud, _GeometryDataFrame]]
        ]
    ]()
    """A collection of collections of variable location data.

    This collection exists to store any spatial data in the scene that joins on the
    variable ``soma_joinid`` for the measurements in the SOMA experiment. The top-level
    collection maps from measurement name to a collection of dataframes.

    Each dataframe in a ``varl`` subcollection can be either a GeometryDataFrame or a
    PointCloud.
    """

    @property
    @abc.abstractmethod
    def coordinate_space(self) -> Optional[coordinates.CoordinateSpace]:
        """Coordinate system for this scene."""
        raise NotImplementedError()

    @coordinate_space.setter
    @abc.abstractmethod
    def coordinate_space(self, value: coordinates.CoordinateSpace) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def register_geometry_dataframe(
        self,
        key: str,
        transform: coordinates.CoordinateTransform,
        *,
        subcollection: Union[str, Sequence[str]] = "obsl",
        coordinate_space: Optional[coordinates.CoordinateSpace] = None,
    ) -> _GeometryDataFrame:
        """Adds the coordinate transform for the scene coordinate space to
        a point cloud stored in the scene.

        If the subcollection the geometry dataframe is inside of is more than one
        layer deep, the input should be provided as a sequence of names. For example,
        to register a geometry dataframe named  "transcripts" in the "var/RNA"
        collection::

            scene.register_geometry_dataframe(
                'transcripts', transform, subcollection=['var', 'RNA'],
            )

        Args:
            key: The name of the geometry dataframe.
            transform: The coordinate transformation from the scene to the dataframe.
            subcollection: The name, or sequence of names, of the subcollection the
                dataframe is stored in. Defaults to ``'obsl'``.
            coordinate_space: Optional coordinate space for the dataframe. This will
                replace the existing coordinate space of the dataframe.

        Returns:
            The registered geometry dataframe in write mode.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def register_multiscale_image(
        self,
        key: str,
        transform: coordinates.CoordinateTransform,
        *,
        subcollection: Union[str, Sequence[str]] = "img",
        coordinate_space: Optional[coordinates.CoordinateSpace] = None,
    ) -> _MultiscaleImage:
        """Adds the coordinate transform for the scene coordinate space to
        a multiscale image stored in the scene.

        The transform to the multiscale image must be to the coordinate space
        defined on the reference level for the image. In most cases, this will be
        the level ``0`` image.

        Args:
            key: The name of the multiscale image.
            transform: The coordinate transformation from the scene to the reference
                level of the multiscale image.
            subcollection: The name, or sequence of names, of the subcollection the
                image is stored in. Defaults to ``'img'``.
            coordinate_space: Optional coordinate space for the image. This will
                replace the existing coordinate space of the multiscale image.

        Returns:
            The registered multiscale image in write mode.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def register_point_cloud(
        self,
        key: str,
        transform: coordinates.CoordinateTransform,
        *,
        subcollection: Union[str, Sequence[str]] = "obsl",
        coordinate_space: Optional[coordinates.CoordinateSpace] = None,
    ) -> _PointCloud:
        """Adds the coordinate transform for the scene coordinate space to
        a point cloud stored in the scene.

        If the subcollection the point cloud is inside of is more than one
        layer deep, the input should be provided as a sequence of names. For example,
        to register a point named `transcripts` in the `var/RNA`
        collection::

            scene.register_point_cloud(
                'transcripts', transform, subcollection=['var', 'RNA'],
            )

        Args:
            key: The name of the point cloud.
            transform: The coordinate transformation from the scene to the point cloud.
            subcollection: The name, or sequence of names, of the subcollection the
                point cloud is stored in. Defaults to ``'obsl'``.
            coordinate_space: Optional coordinate space for the point cloud. This will
                replace the existing coordinate space of the point cloud. Defaults to
                ``None``.

        Returns:
            The registered point cloud in write mode.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_transformation_to_geometry_dataframe(
        self, key: str, *, subcollection: Union[str, Sequence[str]] = "obsl"
    ):
        """Returns the coordinate transformation from the scene to a requested
        geometery dataframe.

        Args:
            key: The name of the geometry dataframe.
            subcollection: The name, or sequence of names, of the subcollection the
                dataframe is stored in. Defaults to ``'obsl'``.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_transformation_to_multiscale_image(
        self,
        key: str,
        *,
        subcollection: str = "img",
        level: Optional[Union[str, int]] = None,
    ) -> coordinates.CoordinateTransform:
        """Returns the coordinate transformation from the scene to a requested
        multiscale image.

        Args:
            key: The name of the multiscale image.
            subcollection: The name, or sequence of names, of the subcollection the
                dataframe is stored in. Defaults to ``'img'``.
            level: The level of the image to get the transformation to.
                Defaults to ``None`` -- the transformation will be to the reference
                level.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_transformation_to_point_cloud(
        self, key: str, *, subcollection: str = "obsl"
    ) -> coordinates.CoordinateTransform:
        """Returns the coordinate transformation from the scene to a requested
        geometery dataframe.

        Args:
            key: The name of the point cloud.
            subcollection: The name, or sequence of names, of the subcollection the
                point cloud is stored in. Defaults to ``'obsl'``.
        """
        raise NotImplementedError()
