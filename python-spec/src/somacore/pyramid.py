"""Implementation of the SOMA pyramid image collection for spatial data"""

import abc
from typing import Generic, Optional, TypeVar

import pyarrow as pa
from typing_extensions import Final

from . import base
from . import collection
from . import data
from . import options

_DenseND = TypeVar("_DenseND", bound=data.DenseNDArray)
"""A particular implementation of a collection of DenseNDArrays."""
_RootSO = TypeVar("_RootSO", bound=base.SOMAObject)

_RO_AUTO = options.ResultOrder.AUTO


class Pyramid(
    collection.BaseCollection[_RootSO],
    Generic[_DenseND, _RootSO],
):
    """TODO: Add documentation for pyramid image collection

    Lifecycle: experimental
    """

    # This class is implemented as a mixin to be used with SOMA classes.
    # For example, a SOMA implementation would look like this:
    #
    #     # This type-ignore comment will always be needed due to limitations
    #     # of type annotations; it is (currently) expected.
    #     class Pyramid(  # type: ignore[type-var]
    #         ImplBaseCollection[ImplSOMAObject],
    #         somacore.Pyramid[
    #             ImplDF,           # _SpatialColl
    #             ImplNDArray       # _NDColl
    #             ImplSOMAObject,   # _RootSO
    #         ],
    #     ):
    #         ...

    __slots__ = ()
    soma_type: Final = "SOMAPyramid"  # type: ignore[misc]

    @abc.abstractmethod
    def read_level(
        self,
        level: int,
        coords: options.DenseNDCoords = (),
        *,
        transform: Optional[str] = None,  # TODO: Add/accept transform class
        coordinate_system: Optional[str] = None,
        result_order: options.ResultOrderStr = _RO_AUTO,
        platform_config: Optional[options.PlatformConfig] = None,
    ) -> pa.Tensor:
        """TODO: Add read_image_level documentation"""
        raise NotImplementedError()
