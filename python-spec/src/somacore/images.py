"""Implementation of the SOMA image collection for spatial data"""

import abc
from typing import Generic, Optional, Sequence, Tuple, TypeVar

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


class ImageCollection(
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
    #     class ImageCollection(  # type: ignore[type-var]
    #         ImplBaseCollection[ImplSOMAObject],
    #         somacore.ImageCollection[ImplDenseNDArray, ImpSOMAObject],
    #     ):
    #         ...

    __slots__ = ()
    soma_type: Final = "SOMAImageCollection"  # type: ignore[misc]

    class LevelProperties(Protocol):
        """Class requirements for level properties of images."""

        @property
        def name(self) -> str:
            """The key for the image."""

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
    ) -> data.DenseNDArray:
        """TODO: Add dcoumentation."""
        raise NotImplementedError()

    @property
    def axis_order(self) -> str:
        """The order of the axes in the stored images."""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def level_count(self) -> int:
        """The number of image levels stored in the ImageCollection."""
        raise NotImplementedError()

    @abc.abstractmethod
    def level_properties(self, level: int) -> LevelProperties:
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
