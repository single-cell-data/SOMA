"""Implementation of the SOMA image collection for spatial data"""

import abc
from dataclasses import dataclass
from typing import (
    Any,
    Generic,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

import pyarrow as pa
from typing_extensions import Final, Protocol, Self

from . import base
from . import coordinates
from . import data
from . import options

_DenseND = TypeVar("_DenseND", bound=data.DenseNDArray)
"""A particular implementation of a collection of DenseNDArrays."""
_RootSO = TypeVar("_RootSO", bound=base.SOMAObject)
"""The root SomaObject type of the implementation."""

_RO_AUTO = options.ResultOrder.AUTO
#
# Read types
#

_ReadData = TypeVar("_ReadData")


class PointCloudDataFrame(base.SOMAObject, metaclass=abc.ABCMeta):
    """A specialized SOMA DataFrame for storing collections of points in
    multi-dimensional space.

    The ``PointCloudDataFrame`` class is designed to efficiently store and query point
    data, where each point is represented by coordinates in one or more spatial
    dimensions (e.g., x, y, z) and may have additional columns for associated
    attributes.

    Lifecycle: experimental
    """

    __slots__ = ()
    soma_type: Final = "SOMAPointCloudDataFrame"  # type: ignore[misc]

    @classmethod
    @abc.abstractmethod
    def create(
        cls,
        uri: str,
        *,
        schema: pa.Schema,
        index_column_names: Sequence[str] = (options.SOMA_JOINID, "x", "y"),
        axis_names: Sequence[str] = ("x", "y"),
        domain: Optional[Sequence[Optional[Tuple[Any, Any]]]] = None,
        platform_config: Optional[options.PlatformConfig] = None,
        context: Optional[Any] = None,
    ) -> Self:
        """Creates a new ``PointCloudDataFrame`` at the given URI.

        The schema of the created point cloud  will include a column named
        ``soma_joinid`` of type ``pyarrow.int64``, with negative values disallowed, and
        at least one axis with numeric type.  If a ``soma_joinid`` column is
        present in the provided schema, it must be of the correct type.  If the
        ``soma_joinid`` column is not provided, one will be added. The ``soma_joinid``
        may be an index column. The axis columns must be index columns.

        Args:
            uri: The URI where the dataframe will be created.
            schema: Arrow schema defining the per-column schema. This schema
                must define all columns, including columns to be named as index
                columns.  If the schema includes types unsupported by the SOMA
                implementation, an error will be raised.
            index_column_names: A list of column names to use as user-defined index
                columns (e.g., ``['x', 'y']``). All named columns must exist in the
                schema, and at least one index column name is required.
            axis_names: An ordered list of axis column names that correspond to the
                names of axes of the the coordinate space the points are defined on.
                Must be the name of index columns.
            domain: An optional sequence of tuples specifying the domain of each
                index column. Each tuple should be a pair consisting of the minimum
                and maximum values storable in the index column. If omitted entirely,
                or if ``None`` in a given dimension, the corresponding index-column
                domain will use the minimum and maximum possible values for the
                column's datatype.  This makes a point cloud dataframe growable.

        Returns:
            The newly created geometry dataframe, opened for writing.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    # Data operations

    @abc.abstractmethod
    def read(
        self,
        coords: options.SparseDFCoords = (),
        column_names: Optional[Sequence[str]] = None,
        *,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: options.ResultOrderStr = _RO_AUTO,
        value_filter: Optional[str] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> data.ReadIter[pa.Table]:
        """Reads a user-defined slice of data into Arrow tables.

        Args:
            coords: for each index dimension, which rows to read.
                Defaults to ``()``, meaning no constraint -- all IDs.
            column_names: the named columns to read and return.
                Defaults to ``None``, meaning no constraint -- all column names.
            partitions: If present, specifies that this is part of
                a partitioned read, and which part of the data to include.
            result_order: the order to return results, specified as a
                :class:`~options.ResultOrder` or its string value.
            value_filter: an optional value filter to apply to the results.
                The default of ``None`` represents no filter. Value filter
                syntax is implementation-defined; see the documentation
                for the particular SOMA implementation for details.
        Returns:
            A :class:`ReadIter` of :class:`pa.Table`s.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def read_spatial_region(
        self,
        region: Optional[options.SpatialRegion] = None,
        column_names: Optional[Sequence[str]] = None,
        *,
        region_transform: Optional[coordinates.CoordinateTransform] = None,
        region_coord_space: Optional[coordinates.CoordinateSpace] = None,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: options.ResultOrderStr = _RO_AUTO,
        value_filter: Optional[str] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> "SpatialRead[data.ReadIter[pa.Table]]":
        """Reads data intersecting an user-defined region of space into a
        :class:`SpatialRead` with data in Arrow tables.


        Args:
            region: The region to query. May be a box in the form
                [x_min, y_min, x_max, y_max] (for 2D images), a box in the form
                [x_min, y_min, z_min, x_max, y_max, z_max] (for 3D images), or
                a shapely Geometry.
            column_names: The named columns to read and return.
                Defaults to ``None``, meaning no constraint -- all column names.
            region_transform: An optional coordinate transform from the read region to the
                coordinate system of the spatial dataframe.
                Defaults to ``None``, meaning an identity transform.
            region_coord_space: An optional coordinate space for the region being read.
                Defaults to ``None``, coordinate space will be inferred from transform.
            batch_size: The size of batched reads.
                Defaults to `unbatched`.
            partitions: If present, specifies that this is part of a partitioned read,
                and which part of the data to include.
            result_order: the order to return results, specified as a
                :class:`~options.ResultOrder` or its string value.
            value_filter: an optional value filter to apply to the results.
                The default of ``None`` represents no filter. Value filter
                syntax is implementation-defined; see the documentation
                for the particular SOMA implementation for details.

        Returns:
            A :class:`SpatialRead` with :class:`ReadIter` of :class:`pa.Table`s data.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def write(
        self,
        values: Union[pa.RecordBatch, pa.Table],
        *,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> Self:
        """Writes the data from an Arrow table to the persistent object.

        As duplicate index values are not allowed, index values already present
        in the object are overwritten and new index values are added.

        Args:
            values: An Arrow table containing all columns, including
                the index columns. The schema for the values must match
                the schema for the ``DataFrame``.

        Returns: ``self``, to enable method chaining.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    # Metadata operations

    @property
    @abc.abstractmethod
    def schema(self) -> pa.Schema:
        """The schema of the data in this dataframe.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def index_column_names(self) -> Tuple[str, ...]:
        """The names of the index (dimension) columns.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def coordinate_space(self) -> coordinates.CoordinateSpace:
        """Coordinate space for this point cloud.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @coordinate_space.setter
    @abc.abstractmethod
    def coordinate_space(self, value: coordinates.CoordinateSpace) -> None:
        """Coordinate space for this point cloud.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def axis_names(self) -> Tuple[str, ...]:
        """The names of the axes of the coordinate space the data is defined on.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def domain(self) -> Tuple[Tuple[Any, Any], ...]:
        """The allowable range of values in each index column.

        Returns: a tuple of minimum and maximum values, inclusive,
            storable on each index column of the dataframe.

        Lifecycle: experimental
        """
        raise NotImplementedError()


class GeometryDataFrame(base.SOMAObject, metaclass=abc.ABCMeta):
    """A specialized SOMA object for storing complex geometries with spatial indexing.

    The ``GeometryDataFrame`` class is designed to store and manage geometric shapes such as
    polygons, lines, and multipoints, along with additional columns for associated attributes.

    Lifecycle: experimental
    """

    __slots__ = ()
    soma_type: Final = "SOMAGeometryDataFrame"  # type: ignore[misc]

    # Lifecycle

    @classmethod
    @abc.abstractmethod
    def create(
        cls,
        uri: str,
        *,
        schema: pa.Schema,
        index_column_names: Sequence[str] = (
            options.SOMA_JOINID,
            options.SOMA_GEOMETRY,
        ),
        axis_names: Sequence[str] = ("x", "y"),
        domain: Optional[Sequence[Optional[Tuple[Any, Any]]]] = None,
        platform_config: Optional[options.PlatformConfig] = None,
        context: Optional[Any] = None,
    ) -> Self:
        """Creates a new ``GeometryDataFrame`` at the given URI.

        The schema of the created geometry dataframe will include a column named
        ``soma_joinid`` of type ``pyarrow.int64``, with negative values
        disallowed, and a column named ``soma_geometry of type ``pyarrow.binary`` or
        ``pyarrow.large_binary``.  If a ``soma_joinid`` column or ``soma_geometry``
        are present in the provided schema, they must be of the correct type.  If
        either the ``soma_joinid`` column or ``soma_geometry`` column are not provided,
        one will be added. The ``soma_joinid`` may be an index column. The
        ``soma_geometry`` column must be an index column.

        Args:
            uri: The URI where the dataframe will be created.
            schema: Arrow schema defining the per-column schema. This schema
                must define all columns, including columns to be named as index
                columns.  If the schema includes types unsupported by the SOMA
                implementation, an error will be raised.
            index_column_names: A list of column names to use as user-defined
                index columns (e.g., ``['cell_type', 'tissue_type']``).
                All named columns must exist in the schema, and at least one
                index column name is required.
            axis_names: An ordered list of axis column names that correspond to the
                names of the axes of the coordinate space the geometries are defined
                on.
            domain: An optional sequence of tuples specifying the domain of each
                index column. Two tuples must be provided for the ``soma_geometry``
                column which store the width followed by the height. Each tuple should
                be a pair consisting of the minimum and maximum values storable in the
                index column. If omitted entirely, or if ``None`` in a given dimension,
                the corresponding index-column domain will use the minimum and maximum
                possible values for the column's datatype.  This makes a dataframe
                growable.

        Returns:
            The newly created geometry dataframe, opened for writing.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    # Data operations

    @abc.abstractmethod
    def read(
        self,
        coords: options.SparseDFCoords = (),
        column_names: Optional[Sequence[str]] = None,
        *,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: options.ResultOrderStr = _RO_AUTO,
        value_filter: Optional[str] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> data.ReadIter[pa.Table]:
        """Reads a user-defined slice of data into Arrow tables.

        Args:
            coords: for each index dimension, which rows to read.
                Defaults to ``()``, meaning no constraint -- all IDs.
            column_names: the named columns to read and return.
                Defaults to ``None``, meaning no constraint -- all column names.
            partitions: If present, specifies that this is part of
                a partitioned read, and which part of the data to include.
            result_order: the order to return results, specified as a
                :class:`~options.ResultOrder` or its string value.
            value_filter: an optional value filter to apply to the results.
                The default of ``None`` represents no filter. Value filter
                syntax is implementation-defined; see the documentation
                for the particular SOMA implementation for details.
        Returns:
            A :class:`ReadIter` of :class:`pa.Table`s.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def read_spatial_region(
        self,
        region: Optional[options.SpatialRegion] = None,
        column_names: Optional[Sequence[str]] = None,
        *,
        region_transform: Optional[coordinates.CoordinateTransform] = None,
        region_coord_space: Optional[coordinates.CoordinateSpace] = None,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: options.ResultOrderStr = _RO_AUTO,
        value_filter: Optional[str] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> "SpatialRead[data.ReadIter[pa.Table]]":
        """Reads data intersecting an user-defined region of space into a
        :class:`SpatialRead` with data in Arrow tables.


        Args:
            region: The region to query. May be a box in the form
                [x_min, y_min, x_max, y_max] (for 2D images), a box in the form
                [x_min, y_min, z_min, x_max, y_max, z_max] (for 3D images), or
                a shapely Geometry.
            column_names: The named columns to read and return.
                Defaults to ``None``, meaning no constraint -- all column names.
            region_transform: An optional coordinate transform from the read region to the
                coordinate system of the spatial dataframe.
                Defaults to ``None``, meaning an identity transform.
            region_coord_space: An optional coordinate space for the region being read.
                Defaults to ``None``, coordinate space will be inferred from transform.
            batch_size: The size of batched reads.
                Defaults to `unbatched`.
            partitions: If present, specifies that this is part of a partitioned read,
                and which part of the data to include.
            result_order: the order to return results, specified as a
                :class:`~options.ResultOrder` or its string value.
            value_filter: an optional value filter to apply to the results.
                The default of ``None`` represents no filter. Value filter
                syntax is implementation-defined; see the documentation
                for the particular SOMA implementation for details.

        Returns:
            A :class:`SpatialRead` with :class:`ReadIter` of :class:`pa.Table`s data.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def write(
        self,
        values: Union[pa.RecordBatch, pa.Table],
        *,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> Self:
        """Writes the data from an Arrow table to the persistent object.

        As duplicate index values are not allowed, index values already present
        in the object are overwritten and new index values are added.

        Args:
            values: An Arrow table containing all columns, including
                the index columns. The schema for the values must match
                the schema for the ``DataFrame``.

        Returns: ``self``, to enable method chaining.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    # Metadata operations

    @property
    @abc.abstractmethod
    def schema(self) -> pa.Schema:
        """The schema of the data in this dataframe.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def index_column_names(self) -> Tuple[str, ...]:
        """The names of the index (dimension) columns.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def axis_names(self) -> Tuple[str, ...]:
        """The names of the axes of the coordinate space the data is defined on.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def coordinate_space(self) -> coordinates.CoordinateSpace:
        """Coordinate space for this geometry dataframe.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @coordinate_space.setter
    @abc.abstractmethod
    def coordinate_space(self, value: coordinates.CoordinateSpace) -> None:
        """Coordinate space for this geometry dataframe.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def domain(self) -> Tuple[Tuple[Any, Any], ...]:
        """The allowable range of values in each index column.

        Returns: a tuple of minimum and maximum values, inclusive,
            storable on each index column of the dataframe.

        Lifecycle: experimental
        """
        raise NotImplementedError()


class MultiscaleImage(  # type: ignore[misc]  # __eq__ false positive
    base.SOMAObject,
    Generic[_DenseND, _RootSO],
    MutableMapping[str, _DenseND],
    metaclass=abc.ABCMeta,
):
    """A multiscale image with an extendable number of resolution levels.

    The multiscale image defines the top level properties. Each level must
    match the expected following properties:
    * number of channels
    * axis order

    Lifecycle: experimental
    """

    # This class is implemented as a mixin to be used with SOMA classes.
    # For example, a SOMA implementation would look like this:
    #
    #     # This type-ignore comment will always be needed due to limitations
    #     # of type annotations; it is (currently) expected.
    #     class MultiscaleImage(  # type: ignore[type-var]
    #         ImplBaseCollection[ImplSOMAObject],
    #         somacore.MultiscaleImage[ImplDenseNDArray, ImpSOMAObject],
    #     ):
    #         ...

    soma_type: Final = "SOMAMultiscaleImage"  # type: ignore[misc]
    __slots__ = ()

    # Lifecycle

    @classmethod
    @abc.abstractmethod
    def create(
        cls,
        uri: str,
        *,
        type: pa.DataType,
        reference_level_shape: Sequence[int],
        axis_names: Sequence[str] = ("c", "y", "x"),
        axis_types: Sequence[str] = ("channel", "height", "width"),
        platform_config: Optional[options.PlatformConfig] = None,
        context: Optional[Any] = None,
    ) -> Self:
        """Creates a new collection of this type at the given URI.

        Args:
            uri: The URI where the collection will be created.
            reference_level_shape: The shape of the reference level for the multiscale
                image. In most cases, this corresponds to the size of the image
                at ``level=0``.
            axis_names: The names of the axes of the image.
            axis_types: The types of the axes of the image. Must be the same length as
                ``axis_names``. Valid types are: ``channel``, ``height``, ``width``,
                and ``depth``.

        Returns:
            The newly created collection, opened for writing.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def add_new_level(
        self,
        key: str,
        *,
        uri: Optional[str] = None,
        shape: Sequence[int],
    ) -> data.DenseNDArray:
        """Add a new level in the multi-scale image.

        Parameters are as in :meth:`data.DenseNDArray.create`. The provided shape will
        be used to compute the scale between images and must correspond to the image
        size for the entire image.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    # Data operations

    @abc.abstractmethod
    def read_spatial_region(
        self,
        level: Union[int, str],
        region: options.SpatialRegion = (),
        *,
        channel_coords: options.DenseCoord = None,
        region_transform: Optional[coordinates.CoordinateTransform] = None,
        region_coord_space: Optional[coordinates.CoordinateSpace] = None,
        result_order: options.ResultOrderStr = _RO_AUTO,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> "SpatialRead[pa.Tensor]":
        """Reads a user-defined region of space into a :class:`SpatialRead` with data
        in either an Arrow tensor or table.

        Reads the bounding box of the input region from the requested image level. This
        will return a :class:`SpatialRead` with the image data stored as a
        :class:`pa.Tensor`.

        Args:
            level: The image level to read the data from. May use index of the level
                or the image name.
            region: The region to query. May be a box in the form
                [x_min, y_min, x_max, y_max] (for 2D images), a box in the form
                [x_min, y_min, z_min, x_max, y_max, z_max] (for 3D images), or
                a shapely Geometry.
            channel_coords: An optional slice that defines the channel coordinates
                to read.
            region_transform: An optional coordinate transform that provides the
                transformation from the provided region to the reference level of this
                image. Defaults to ``None``.
            region_coord_space: An optional coordinate space for the region being read.
                The axis names must match the input axis names of the transform.
                Defaults to ``None``, coordinate space will be inferred from transform.
            result_order: the order to return results, specified as a
                :class:`~options.ResultOrder` or its string value.

        Returns:
            The data bounding the requested region as a :class:`SpatialRead` with
            :class:`pa.Tensor` data.
        """
        raise NotImplementedError()

    # Metadata operations

    @property
    @abc.abstractmethod
    def axis_names(self) -> Tuple[str, ...]:
        """The name of the image axes.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def coordinate_space(self) -> coordinates.CoordinateSpace:
        """Coordinate space for this multiscale image.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @coordinate_space.setter
    @abc.abstractmethod
    def coordinate_space(self, value: coordinates.CoordinateSpace) -> None:
        """Coordinate space for this multiscale image.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_transform_from_level(
        self, level: Union[int, str]
    ) -> coordinates.ScaleTransform:
        """Returns the transformation from user requested level to image reference level.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_transform_to_level(
        self, level: Union[int, str]
    ) -> coordinates.ScaleTransform:
        """Returns the transformation from the image reference level to the user
        requested level.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def image_type(self) -> str:
        """The order of the axes as stored in the data model.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def level_count(self) -> int:
        """The number of image levels stored in the MultiscaleImage.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def level_properties(self, level: Union[int, str]) -> "ImageProperties":
        """The properties of an image at the specified level.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @property
    def reference_level(self) -> Optional[int]:
        """The index of image level that is used as a reference level.

        This will return ``None`` if no current image level matches the size of the
        reference level.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def reference_level_properties(self) -> "ImageProperties":
        """The image properties of the reference level.

        Lifecycle: experimental
        """
        raise NotImplementedError()


class ImageProperties(Protocol):
    """Class requirements for level properties of images.

    Lifecycle: experimental
    """

    @property
    def name(self) -> str:
        """The key for the image.

        Lifecycle: experimental
        """

    @property
    def shape(self) -> Tuple[int, ...]:
        """Size of each axis of the image.

        Lifecycle: experimental
        """


@dataclass
class SpatialRead(Generic[_ReadData]):
    """Reader for spatial data.

    Args:
        data: The data accessor.
        data_coordinate_space: The coordinate space the read data is defined on.
        output_coordinate_space: The requested output coordinate space.
        coordinate_transform: A coordinate transform from the data coordinate space to
            the desired output coordinate space.

    Lifecycle: experimental
    """

    data: _ReadData
    data_coordinate_space: coordinates.CoordinateSpace
    output_coordinate_space: coordinates.CoordinateSpace
    coordinate_transform: coordinates.CoordinateTransform

    def __post_init__(self):
        if (
            self.data_coordinate_space.axis_names
            != self.coordinate_transform.input_axes
        ):
            raise ValueError(
                "Input coordinate transform axis names do not match the data coordinate "
                "space."
            )
        if (
            self.output_coordinate_space.axis_names
            != self.coordinate_transform.output_axes
        ):
            raise ValueError(
                "Output coordinate transform axis names do not match the output "
                "coordinate space."
            )
