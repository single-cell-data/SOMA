"""Implementation of the SOMA image collection for spatial data"""

import abc
from typing import Generic, Optional, Sequence, Tuple, TypeVar, Union

import pyarrow as pa
from typing_extensions import Final, Protocol

from . import base
from . import collection
from . import coordinates
from . import data
from . import options

_DenseND = TypeVar("_DenseND", bound=data.DenseNDArray)
"""A particular implementation of a collection of DenseNDArrays."""
_RootSO = TypeVar("_RootSO", bound=base.SOMAObject)
"""The root SomaObject type of the implementation."""

_RO_AUTO = options.ResultOrder.AUTO


class Image2DCollection(
    collection.BaseCollection[_RootSO],
    Generic[_DenseND, _RootSO],
):
    """TODO: Add documentation for image collection

    Lifecycle: experimental
    """

    # This class is implemented as a mixin to be used with SOMA classes.
    # For example, a SOMA implementation would look like this:
    #
    #     # This type-ignore comment will always be needed due to limitations
    #     # of type annotations; it is (currently) expected.
    #     class Image2DCollection(  # type: ignore[type-var]
    #         ImplBaseCollection[ImplSOMAObject],
    #         somacore.Image2DCollection[ImplDenseNDArray, ImpSOMAObject],
    #     ):
    #         ...

    __slots__ = ()
    soma_type: Final = "SOMAImage2DCollection"  # type: ignore[misc]

    class LevelProperties(Protocol):
        """Class requirements for level properties of 2D images."""

        @property
        def axis_order(self) -> Tuple[str, ...]:
            """Axis order for the underlying data.

            Must contain 'X' and 'Y' for single-channel images and 'X', 'Y', and 'C'
            for multi-channel images. Here `X' denotes the axis along the width of
            the image and `Y' denotes the axis along the height of an image.
            """

        @property
        def name(self) -> str:
            """The key for the level inside the Image2DCollection."""

        @property
        def shape(self) -> Tuple[int, ...]:
            """Number of pixels for each dimension of the image."""

    @abc.abstractmethod
    def add_new_level(
        self,
        key: str,
        *,
        uri: Optional[str] = None,
        type: pa.DataType,
        shape: Sequence[int],
        axis_order: Union[str, Sequence[str]],
    ) -> data.DenseNDArray:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def level_count(self) -> int:
        raise NotImplementedError()

    @abc.abstractmethod
    def level_properties(self, level: int) -> LevelProperties:
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
