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

    class LevelProperties(Protocol):
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
            """Number of pixels for each dimension of the image.

            Lifecycle: experimental
            """

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

    @property
    @abc.abstractmethod
    def axis_names(self) -> Tuple[str, ...]:
        # TODO: Add docstring
        raise NotImplementedError()

    @abc.abstractmethod
    def add_new_level(
        self,
        key: str,
        *,
        uri: Optional[str] = None,
        type: pa.DataType,  # TODO: Remove this option
        shape: Sequence[int],
    ) -> data.DenseNDArray:
        """Add a new level in the multi-scale image.

        Parameters are as in :meth:`data.DenseNDArray.create`. The provided shape will
        be used to compute the scale between images and must correspond to the image
        size for the entire image.

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
        """The number of image levels stored in the MultiscaleImage."""
        raise NotImplementedError()

    @abc.abstractmethod
    def level_properties(self, level: Union[int, str]) -> LevelProperties:
        """The properties of an image at the specified level."""
        raise NotImplementedError()

    @abc.abstractmethod
    def read_level(
        self,
        level: int,
        coords: options.DenseNDCoords = (),
        *,
        transform: Optional[coordinates.CoordinateTransform] = None,
        result_order: options.ResultOrderStr = _RO_AUTO,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> pa.Tensor:
        """TODO: Add read_image_level documentation"""
        raise NotImplementedError()

    @property
    def reference_level(self) -> Optional[int]:
        """TODO: Add docstring"""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def reference_level_shape(self) -> Optional[Tuple[int, ...]]:
        """The reference shape for this multiscale image pyramid.

        In most cases this should correspond to the shape of the image at level 0. If
        ``data_axis_order`` is not ``None``, the shape will be in the same order as the
        data as stored on disk.

        Lifecycle: experimental
        """
        raise NotImplementedError()
