"""Implementation of the SOMA image collection for spatial data"""

import abc
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


class SpatialDataFrame(base.SOMAObject, metaclass=abc.ABCMeta):
    """A multi-column table with spatial indexing and a user-defined schema.

    Lifecycle: experimental
    """

    __slots__ = ()

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
    def spatial_read(
        self,
        region: options.SpatialDFCoords = (),
        column_names: Optional[Sequence[str]] = None,
        *,
        transform: Optional[coordinates.CoordinateTransform] = None,
        batch_size: options.BatchSize = options.BatchSize(),
        partitions: Optional[options.ReadPartitions] = None,
        result_order: options.ResultOrderStr = _RO_AUTO,
        value_filter: Optional[str] = None,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> "SpatialReadIter[pa.Table]":
        """Reads a user-defined slice of data into Arrow tables.

        TODO: Add details about the requested input region.
        TODO: Add details about the output SpatialReadIter.

        Args:
            region: for each index dimension, which rows to read or a single shape.
                Defaults to ``()``, meaning no constraint -- all IDs.
            column_names: the named columns to read and return.
                Defaults to ``None``, meaning no constraint -- all column names.
            transform: coordinate transform to apply to results.
                Defaults to ``None``, meaning an identity transform.
            batch_size: The size of batched reads.
                Defaults to `unbatched`.
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
    def domain(self) -> Tuple[Tuple[Any, Any], ...]:
        """The allowable range of values in each index column.

        Returns: a tuple of minimum and maximum values, inclusive,
            storable on each index column of the dataframe.

        Lifecycle: experimental
        """
        raise NotImplementedError()


class PointCloud(SpatialDataFrame, metaclass=abc.ABCMeta):
    """A multi-column table with point data and a user-defined schema.

    Lifecycle: experimental
    """

    __slots__ = ()
    soma_type: Final = "SOMAPointCloud"  # type: ignore[misc]

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
        """Creates a new ``PointCloud`` at the given URI.

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

            axis_names: An ordered list of axis column names that
                coorespond to the names of axes of the the coordinate space the points
                are defined on.

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


class GeometryDataFrame(SpatialDataFrame, metaclass=abc.ABCMeta):
    """A multi-column table of geometries with spatial indexing and a user-defined
    schema.

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

        The schema of the created geoemetry dataframe will include a column named
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

            axis_names: An ordered list of axis column names that
                coorespond to the names of the axes of the coordinate space the
                geometries are defined on.

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


class MultiscaleImage(  # type: ignore[misc]  # __eq__ false positive
    base.SOMAObject,
    Generic[_DenseND, _RootSO],
    MutableMapping[str, _DenseND],
    metaclass=abc.ABCMeta,
):
    """TODO: Add documentation for image collection

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
        image_type: str = "CYX",
        reference_level_shape: Sequence[int],
        axis_names: Sequence[str] = ("c", "x", "y"),
        platform_config: Optional[options.PlatformConfig] = None,
        context: Optional[Any] = None,
    ) -> Self:
        """Creates a new collection of this type at the given URI.

        Args:
            uri: The URI where the collection will be created.
            axis_names: The names of the axes of the image.
            reference_level_shape: # TODO
            image_type: The order of the image axes # TODO

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
    def read_level(
        self,
        level: Union[int, str],
        region: options.ImageCoords = (),
        *,
        transform: Optional[coordinates.CoordinateTransform] = None,
        result_order: options.ResultOrderStr = _RO_AUTO,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> "SpatialReadIter[pa.Tensor]":
        """Reads a user-defined slice or region into a Tensor.

        Input query region may be a geometric shape or coordinates.
        Coordinates must specify a contiguous subarray, and the number of
        coordinates must be less than or equal to the number of dimensions.
        For example, if the array is 10×20, acceptable values of ``coords``
        include ``()``, ``(3, 4)``, ``[slice(5, 10)]``, and
        ``[slice(5, 10), slice(6, 12)]``. The requested region is specified in the
        transformed space.

        The returned data will take the bounding box of the requested region with the
        box parallel to the image coordinates.

        TODO: Add details about the output SpatialReadIter.

        TODO: Add arguments.

        Returns:
            A :class:`SpatialReadIter` or :class:`pa.Tensor`s.
        """
        raise NotImplementedError()

    # Metadata opeations

    @property
    @abc.abstractmethod
    def axis_names(self) -> Tuple[str, ...]:
        """The name of the image axes.

        Lifecycle: experimental
        """
        raise NotImplementedError()

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
        """Coordinate system for this scene.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_transformation_from_level(
        self, level: Union[int, str]
    ) -> coordinates.ScaleTransform:
        """Returns the transformation from the MultiscaleImage base coordinate
        system to the requested level.

        If ``reference_shape`` is set, this will be the scale transformation from the
        ``reference_shape`` to the requested level. If ``reference_shape`` is not set,
        the transformation will be to from the level 0 image to the reequence level.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_transformation_to_level(
        self, level: Union[int, str]
    ) -> coordinates.ScaleTransform:
        """Returns the transformation from the MultiscaleImage base coordinate
        system to the requested level.

        If ``reference_shape`` is set, this will be the scale transformation from the
        ``reference_shape`` to the requested level. If ``reference_shape`` is not set,
        the transformation will be to from the level 0 image to the reequence level.

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
        """TODO: Add docstring"""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def reference_level_properties(self) -> "ImageProperties":
        """The reference shape for this multiscale image pyramid.

        In most cases this should correspond to the shape of the image at level 0. If
        ``data_axis_order`` is not ``None``, the shape will be in the same order as the
        data as stored on disk.

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
    def image_type(self) -> str:
        """A string describing the axis order of the image data.

        A valid image type is a permuation of 'YX', 'YXC', 'YXZ', or 'YXZC'. The
        letters have the following meanings:

        * 'X' - image width
        * 'Y' - image height
        * 'Z' - image depth (for three dimensional images)
        * 'C' - channels/bands

        Lifecycle: experimental
        """

    @property
    def shape(self) -> Tuple[int, ...]:
        """Size of each axis of the image.

        Lifecycle: experimental
        """


#
# Read types
#

_T = TypeVar("_T")


# Sparse reads are returned as an iterable structure:


class SpatialReadIter(Generic[_T], metaclass=abc.ABCMeta):

    __slots__ = ()

    # __iter__ is already implemented as `return self` in Iterator.
    # SOMA implementations must implement __next__.

    @property
    @abc.abstractmethod
    def data(self) -> data.ReadIter[_T]:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def data_coordinate_space(self) -> coordinates.CoordinateSpace:
        """The coordinate space of the returned data."""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def output_coordinate_space(self) -> coordinates.CoordinateSpace:
        """The coordinate space the data is being read into."""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def coordinate_transform(self) -> coordinates.CoordinateTransform:
        """A coordinate transform from the coordinate system of the data
        as returned to the requested coordinate system."""
        raise NotImplementedError()
