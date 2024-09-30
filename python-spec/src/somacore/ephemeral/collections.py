from typing import (
    Any,
    Dict,
    Iterator,
    NoReturn,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

import pyarrow as pa
from typing_extensions import Literal, Self

from .. import base
from .. import collection
from .. import coordinates
from .. import data
from .. import experiment
from .. import measurement
from .. import options
from .. import scene
from .. import spatial

_Elem = TypeVar("_Elem", bound=base.SOMAObject)


class BaseCollection(collection.BaseCollection[_Elem]):
    """A memory-backed SOMA Collection for ad-hoc collection building.

    This Collection implementation exists purely in memory. It can be used to
    build ad-hoc SOMA Collections for one-off analyses, and to combine SOMA
    datasets from different sources that cannot be added to a Collection that
    is represented in storage.

    Entries added to this Collection are not "owned" by the collection; their
    lifecycle is still dictated by the place they were opened from. This
    collection has no ``context`` and ``close``ing it does nothing.
    """

    __slots__ = ("_entries", "_metadata")

    def __init__(self, *args: Any, **kwargs: _Elem):
        """Creates a new Collection.

        Arguments and kwargs are provided as in the ``dict`` constructor.
        """
        self._entries: Dict[str, _Elem] = dict(*args, **kwargs)
        self._metadata: Dict[str, Any] = {}

    @property
    def uri(self) -> str:
        return f"somacore:ephemeral-collection:{id(self):x}"

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    @classmethod
    def open(cls, *args, **kwargs) -> NoReturn:
        del args, kwargs  # All unused
        raise TypeError(
            "Ephemeral collections are in-memory only and cannot be opened."
        )

    @classmethod
    def exists(cls, uri: str, *, context: Any = None) -> Literal[False]:
        del uri, context  # All unused.
        # Ephemeral collections are in-memory only and do not otherwise exist.
        return False

    @classmethod
    def create(cls, *args, **kwargs) -> Self:
        del args, kwargs  # All unused
        # ThisCollection is in-memory only, so just return a new empty one.
        return cls()

    def add_new_collection(self, *args, **kwargs) -> NoReturn:
        del args, kwargs  # All unused
        # TODO: Should we be willing to create Collection-based child elements,
        # like Measurement and Experiment?
        raise TypeError(
            "An ephemeral Collection cannot create its own children;"
            " only existing SOMA objects may be added."
        )

    add_new_dataframe = add_new_collection
    add_new_sparse_ndarray = add_new_collection
    add_new_dense_ndarray = add_new_collection

    @property
    def closed(self) -> bool:
        return False  # With no backing storage, there is nothing to close.

    @property
    def mode(self) -> options.OpenMode:
        return "w"  # This collection is always writable.

    def set(
        self, key: str, value: _Elem, *, use_relative_uri: Optional[bool] = None
    ) -> Self:
        del use_relative_uri  # Ignored.
        self._entries[key] = value
        return self

    def __getitem__(self, key: str) -> _Elem:
        return self._entries[key]

    def __delitem__(self, key: str) -> None:
        del self._entries[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)


class Collection(  # type: ignore[misc]  # __eq__ false positive
    BaseCollection[_Elem], collection.Collection
):
    """An in-memory Collection imposing no semantics on the contents."""

    __slots__ = ()


_BasicAbstractMeasurement = measurement.Measurement[
    data.DataFrame,
    collection.Collection[data.NDArray],
    collection.Collection[data.DenseNDArray],
    collection.Collection[data.SparseNDArray],
    base.SOMAObject,
]
"""The loosest possible constraint of the abstract Measurement type."""

_BasicAbstractScene = scene.Scene[
    spatial.MultiscaleImage,
    spatial.PointCloudDataFrame,
    spatial.GeometryDataFrame,
    base.SOMAObject,
]
"""The loosest possible constraint of the abstract Scene type."""


class Measurement(  # type: ignore[misc]  # __eq__ false positive
    BaseCollection[base.SOMAObject], _BasicAbstractMeasurement
):
    """An in-memory Collection with Measurement semantics."""

    __slots__ = ()


class Scene(  # type: ignore[misc]   # __eq__ false positive
    BaseCollection[base.SOMAObject], _BasicAbstractScene
):
    """An in-memory Collection with Scene semantics."""

    __slots__ = ()

    @property
    def coordinate_space(self) -> coordinates.CoordinateSpace:
        """Coordinate system for this scene."""
        raise NotImplementedError()

    @coordinate_space.setter
    def coordinate_space(self, value: coordinates.CoordinateSpace) -> None:
        raise NotImplementedError()

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
    ) -> spatial.GeometryDataFrame:
        raise NotImplementedError()

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
    ) -> spatial.MultiscaleImage:
        raise NotImplementedError()

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
    ) -> spatial.PointCloudDataFrame:
        raise NotImplementedError()

    def set_transform_to_geometry_dataframe(
        self,
        key: str,
        transform: coordinates.CoordinateTransform,
        *,
        subcollection: Union[str, Sequence[str]] = "obsl",
        coordinate_space: Optional[coordinates.CoordinateSpace] = None,
    ) -> spatial.GeometryDataFrame:
        raise NotImplementedError()

    def set_transform_to_multiscale_image(
        self,
        key: str,
        transform: coordinates.CoordinateTransform,
        *,
        subcollection: Union[str, Sequence[str]] = "img",
        coordinate_space: Optional[coordinates.CoordinateSpace] = None,
    ) -> spatial.MultiscaleImage:
        raise NotImplementedError()

    def set_transform_to_point_cloud_dataframe(
        self,
        key: str,
        transform: coordinates.CoordinateTransform,
        *,
        subcollection: Union[str, Sequence[str]] = "obsl",
        coordinate_space: Optional[coordinates.CoordinateSpace] = None,
    ) -> spatial.PointCloudDataFrame:
        raise NotImplementedError()

    def get_transform_from_geometry_dataframe(
        self, key: str, *, subcollection: Union[str, Sequence[str]] = "obsl"
    ) -> coordinates.CoordinateTransform:
        raise NotImplementedError()

    def get_transform_from_multiscale_image(
        self,
        key: str,
        *,
        subcollection: str = "img",
        level: Optional[Union[str, int]] = None,
    ) -> coordinates.CoordinateTransform:
        raise NotImplementedError()

    def get_transform_from_point_cloud_dataframe(
        self, key: str, *, subcollection: str = "obsl"
    ) -> coordinates.CoordinateTransform:
        raise NotImplementedError()

    def get_transform_to_geometry_dataframe(
        self, key: str, *, subcollection: Union[str, Sequence[str]] = "obsl"
    ) -> coordinates.CoordinateTransform:
        raise NotImplementedError()

    def get_transform_to_multiscale_image(
        self,
        key: str,
        *,
        subcollection: str = "img",
        level: Optional[Union[str, int]] = None,
    ) -> coordinates.CoordinateTransform:
        raise NotImplementedError()

    def get_transform_to_point_cloud_dataframe(
        self, key: str, *, subcollection: str = "obsl"
    ) -> coordinates.CoordinateTransform:
        raise NotImplementedError()


class Experiment(  # type: ignore[misc]  # __eq__ false positive
    BaseCollection[base.SOMAObject],
    experiment.Experiment[
        data.DataFrame,
        collection.Collection[_BasicAbstractMeasurement],
        collection.Collection[_BasicAbstractScene],
        base.SOMAObject,
    ],
):
    """An in-memory Collection with Experiment semantics."""

    __slots__ = ()
