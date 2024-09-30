"""Implementation of the SOMA scene collection for spatial data"""

import abc
from typing import Any, Generic, Optional, Sequence, Tuple, TypeVar, Union

import pyarrow as pa
from typing_extensions import Final

from . import _mixin
from . import base
from . import collection
from . import coordinates
from . import options
from . import spatial

_MultiscaleImage = TypeVar("_MultiscaleImage", bound=spatial.MultiscaleImage)
"""A particular implementation of a multiscale image."""

_PointCloudDataFrame = TypeVar(
    "_PointCloudDataFrame", bound=spatial.PointCloudDataFrame
)
"""A particular implementation of a point cloud."""

_GeometryDataFrame = TypeVar("_GeometryDataFrame", bound=spatial.GeometryDataFrame)
"""A particular implementation of a geometry dataframe."""

_RootSO = TypeVar("_RootSO", bound=base.SOMAObject)
"""The root SomaObject type of the implementation."""


class Scene(
    collection.BaseCollection[_RootSO],
    Generic[_MultiscaleImage, _PointCloudDataFrame, _GeometryDataFrame, _RootSO],
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
    #             ImplPointCloudDataFrame,
    #             ImplGeometryDataFrame,
    #             ImplSOMAObject,
    #         ],
    #     ):
    #         ...

    __slots__ = ()
    soma_type: Final = "SOMAScene"  # type: ignore[misc]

    img = _mixin.item[collection.Collection[_MultiscaleImage]]()
    """A collection of multiscale images backing the spatial data.

    Lifecycle: experimental
    """

    obsl = _mixin.item[
        collection.Collection[Union[_PointCloudDataFrame, _GeometryDataFrame]]
    ]()
    """A collection of observation location data.

    This collection exists to store any spatial data in the scene that joins on the obs
    ``soma_joinid``. Each dataframe in ``obsl`` can be either a PointCloudDataFrame
    or a GeometryDataFrame.

    Lifecycle: experimental
    """

    varl = _mixin.item[
        collection.Collection[
            collection.Collection[Union[_PointCloudDataFrame, _GeometryDataFrame]]
        ]
    ]()
    """A collection of collections of variable location data.

    This collection exists to store any spatial data in the scene that joins on the
    variable ``soma_joinid`` for the measurements in the SOMA experiment. The top-level
    collection maps from measurement name to a collection of dataframes.

    Each dataframe in a ``varl`` subcollection can be either a GeometryDataFrame or a
    PointCloudDataFrame.

    Lifecycle: experimental
    """

    @property
    @abc.abstractmethod
    def coordinate_space(self) -> Optional[coordinates.CoordinateSpace]:
        """Coordinate system for this scene.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @coordinate_space.setter
    @abc.abstractmethod
    def coordinate_space(self, value: coordinates.CoordinateSpace) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def add_geometry_dataframe(
        self,
        key: str,
        subcollection: Union[str, Sequence[str]],
        transform: Optional[coordinates.CoordinateTransform],
        *,
        uri: str,
        schema: pa.Schema,
        index_column_names: Sequence[str] = (
            options.SOMA_JOINID,
            options.SOMA_GEOMETRY,
        ),
        axis_names: Sequence[str] = ("x", "y"),
        domain: Optional[Sequence[Optional[Tuple[Any, Any]]]] = None,
        platform_config: Optional[options.PlatformConfig] = None,
        context: Optional[Any] = None,
    ) -> _GeometryDataFrame:
        """Adds a ``GeometryDataFrame`` to the scene and sets a coordinate transform
        between the scene and the dataframe.

        If the subcollection the geometry dataframe is inside of is more than one
        layer deep, the input should be provided as a sequence of names. For example,
        to set the transformation to a geometry dataframe named  "transcripts" in
        the "var/RNA" collection::

            scene.add_geometry_dataframe(
                'cell_boundaries', subcollection=['var', 'RNA'], **kwargs
            )

        Args:
            key: The name of the geometry dataframe.
            transform: The coordinate transformation from the scene to the dataframe.
            subcollection: The name, or sequence of names, of the subcollection the
                dataframe is stored in. Defaults to ``'obsl'``.

        Returns:
            The newly create ``GeometryDataFrame``, opened for writing.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def add_multiscale_image(
        self,
        key: str,
        subcollection: Union[str, Sequence[str]],
        transform: Optional[coordinates.CoordinateTransform],
        *,
        uri: str,
        type: pa.DataType,
        reference_level_shape: Sequence[int],
        axis_names: Sequence[str] = ("c", "x", "y"),
        axis_types: Sequence[str] = ("channel", "height", "width"),
    ) -> _MultiscaleImage:
        """Adds a ``MultiscaleImage`` to the scene and sets a coordinate transform
        between the scene and the dataframe.

        Parameters are as in :meth:`spatial.PointCloudDataFrame.create`.
        See :meth:`add_new_collection` for details about child URIs.

        Args:
            key: The name of the geometry dataframe.
            transform: The coordinate transformation from the scene to the dataframe.
            subcollection: The name, or sequence of names, of the subcollection the
                dataframe is stored in. Defaults to ``'obsl'``.

        Returns:
            The newly create ``MultiscaleImage``, opened for writing.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def add_new_point_cloud_dataframe(
        self,
        key: str,
        subcollection: Union[str, Sequence[str]],
        transform: Optional[coordinates.CoordinateTransform],
        *,
        uri: Optional[str] = None,
        schema: pa.Schema,
        index_column_names: Sequence[str] = (options.SOMA_JOINID,),
        axis_names: Sequence[str] = ("x", "y"),
        domain: Optional[Sequence[Optional[Tuple[Any, Any]]]] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> _PointCloudDataFrame:
        """Adds a point cloud to the scene and sets a coordinate transform
        between the scene and the dataframe.

        Parameters are as in :meth:`spatial.PointCloudDataFrame.create`.
        See :meth:`add_new_collection` for details about child URIs.

        Args:
            key: The name of the geometry dataframe.
            transform: The coordinate transformation from the scene to the dataframe.
            subcollection: The name, or sequence of names, of the subcollection the
                dataframe is stored in. Defaults to ``'obsl'``.

        Returns:
            The newly created ``PointCloudDataFrame``, opened for writing.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def set_transform_to_geometry_dataframe(
        self,
        key: str,
        transform: coordinates.CoordinateTransform,
        *,
        subcollection: Union[str, Sequence[str]] = "obsl",
        coordinate_space: Optional[coordinates.CoordinateSpace] = None,
    ) -> _GeometryDataFrame:
        """Adds the coordinate transform for the scene coordinate space to
        a geometry dataframe stored in the scene.

        If the subcollection the geometry dataframe is inside of is more than one
        layer deep, the input should be provided as a sequence of names. For example,
        to set a transformation for geometry dataframe named  "transcripts" in the
        "var/RNA" collection::

            scene.set_transfrom_for_geometry_dataframe(
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
            The geometry dataframe, opened for writing.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def set_transform_to_multiscale_image(
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
            The multiscale image, opened for writing.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def set_transform_to_point_cloud_dataframe(
        self,
        key: str,
        transform: coordinates.CoordinateTransform,
        *,
        subcollection: Union[str, Sequence[str]] = "obsl",
        coordinate_space: Optional[coordinates.CoordinateSpace] = None,
    ) -> _PointCloudDataFrame:
        """Adds the coordinate transform for the scene coordinate space to
        a point cloud stored in the scene.

        If the subcollection the point cloud is inside of is more than one
        layer deep, the input should be provided as a sequence of names. For example,
        to set a transform for  a point named `transcripts` in the `var/RNA`
        collection::

            scene.set_transformation_for_point_cloud_dataframe(
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
            The point cloud, opened for writing.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_transform_from_geometry_dataframe(
        self, key: str, *, subcollection: Union[str, Sequence[str]] = "obsl"
    ) -> coordinates.CoordinateTransform:
        """Returns the coordinate transformation from the requested geometry dataframe
        to the scene.

        Args:
            key: The name of the geometry dataframe.
            subcollection: The name, or sequence of names, of the subcollection the
                dataframe is stored in. Defaults to ``'obsl'``.

        Returns:
            Coordinate transform from the dataframe to the scene.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_transform_from_multiscale_image(
        self,
        key: str,
        *,
        subcollection: str = "img",
        level: Optional[Union[str, int]] = None,
    ) -> coordinates.CoordinateTransform:
        """Returns the coordinate transformation from the requested multiscale image to
        the scene.

        Args:
            key: The name of the multiscale image.
            subcollection: The name, or sequence of names, of the subcollection the
                dataframe is stored in. Defaults to ``'img'``.
            level: The level of the image to get the transformation from.
                Defaults to ``None`` -- the transformation will be to the reference
                level.

        Returns:
            Coordinate transform from the multiscale image to the scene.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_transform_from_point_cloud_dataframe(
        self, key: str, *, subcollection: str = "obsl"
    ) -> coordinates.CoordinateTransform:
        """Returns the coordinate transformation from the requested point cloud to
        the scene.

        Args:
            key: The name of the point cloud.
            subcollection: The name, or sequence of names, of the subcollection the
                point cloud is stored in. Defaults to ``'obsl'``.

        Returns:
            Coordinate transform from the scene to the point cloud.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_transform_to_geometry_dataframe(
        self, key: str, *, subcollection: Union[str, Sequence[str]] = "obsl"
    ) -> coordinates.CoordinateTransform:
        """Returns the coordinate transformation from the scene to a requested
        geometery dataframe.

        Args:
            key: The name of the geometry dataframe.
            subcollection: The name, or sequence of names, of the subcollection the
                dataframe is stored in. Defaults to ``'obsl'``.

        Returns:
            Coordinate transform from the scene to the requested dataframe.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_transform_to_multiscale_image(
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

        Returns:
            Coordinate transform from the scene to the requested multiscale image.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_transform_to_point_cloud_dataframe(
        self, key: str, *, subcollection: str = "obsl"
    ) -> coordinates.CoordinateTransform:
        """Returns the coordinate transformation from the scene to a requested
        point cloud.

        Args:
            key: The name of the point cloud.
            subcollection: The name, or sequence of names, of the subcollection the
                point cloud is stored in. Defaults to ``'obsl'``.

        Returns:
            Coordinate transform from the scene to the requested point cloud.

        Lifecycle: experimental
        """
        raise NotImplementedError()
