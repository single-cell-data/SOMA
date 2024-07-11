from typing import Generic, Mapping, Optional, TypeVar

import pyarrow as pa
from typing_extensions import Protocol

from .. import coordinates
from .. import data
from .. import options

_RO_AUTO = options.ResultOrder.AUTO

_Scene = TypeVar("_Scene", bound="_Sceneish")
"""TypeVar for the concrete type of a Scene-like object."""


class SceneSpatialQuery(Generic[_Scene]):
    """TODO: Add docstring"""

    def __init__(
        self,
        scene: _Scene,
        region_of_interest: options.SpatialRegion,
        *,
        coord_system: Optional[str] = None,
    ):
        """Spatial query on the data in a scene.

        TODO: Add more details and examples.

        Parameters:

            scene: The name of the scene to query.

            region_of_interest: The region to query.

            coord_system: The name of the coordinate system the region of interest
                is defined on. If not specified, the default coordinate system is
                used.

        """
        self.scene = scene
        # TODO: Enable this check.
        # if (
        #    coord_system is not None
        #    and coord_system not in self.scene.coordinate_systems
        # ):
        #    raise KeyError(f"No coordinate system '{coord_system}'.")
        self.coord_system = coord_system

    def img(self, layer):
        """TODO: Add documentation for image."""
        raise NotImplementedError()

    def obsl(
        self,
        layer: str,
        *,
        override_transform: Optional[coordinates.CoordinateTransform] = None,
    ) -> data.ReadIter[pa.Table]:
        """TODO: Add docstring"""
        try:
            _obsl = self.scene.obsl
        except KeyError as ke:
            raise ValueError("Scene does not contain obsl data.") from ke

        try:
            _obsl_layer = _obsl[layer]
        except KeyError as ke:
            raise ValueError(f"Layer {layer!r} is not available in obsl.") from ke
        if not isinstance(
            _obsl_layer, data.DataFrame
        ):  # TODO: Update type when GeometryDataFrame is implemented.
            raise TypeError(
                f"Unexpected SOMA type {type(_obsl_layer).__name__} store in obsl "
                f"layer {layer!r}."
            )

        # Query the obsl by spatial region.
        # TODO: Need to figure out the names of the spatial dimensions.
        # return _obsl_layer.read((,))
        raise NotImplementedError()

    def varl(self, measurement_name: str, layer: str) -> data.ReadIter[pa.Table]:
        """TODO: Add docstring"""
        try:
            _varl = self.scene.varl
        except KeyError as ke:
            raise ValueError("Scene does not contain varl data.") from ke

        try:
            _varl_ms = self.scene.varl[measurement_name]
        except KeyError as ke:
            raise ValueError(
                f"No varl measurement data for measurement {measurement_name!r}."
            ) from ke
        try:
            _varl_layer = _varl_ms[layer]
        except KeyError as ke:
            raise ValueError(
                f"Layer {layer!r} is not available in varl for measurment "
                f"{measurement_name!r}."
            ) from ke
        if not isinstance(
            _varl_layer, data.DataFrame
        ):  # TODO Update type when GeometryDataFrame is implemented.
            raise TypeError(
                f"Unexpected SOMA type {type(_varl_layer).__name__} stored in varl "
                f"measurement {measurement_name!r} layer {layer!r}"
            )

        raise NotImplementedError()
        # return _varl_layer.read((,))


class _Sceneish(Protocol):
    """The API we need from a Scene."""

    @property
    def img(self) -> Mapping[str, Mapping[str, data.NDArray]]: ...

    @property
    def obsl(self) -> Mapping[str, data.DataFrame]: ...

    @property
    def varl(self) -> Mapping[str, Mapping[str, data.DataFrame]]: ...
