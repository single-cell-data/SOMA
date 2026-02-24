"""Definitions of types related to coordinate systems."""

from __future__ import annotations

from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class Axis(Protocol):
    """A description of an axis of a coordinate system

    Lifecycle: experimental
    """

    @property
    def name(self) -> str:
        """The name of the axis."""
        ...

    @property
    def unit(self) -> str | None:
        """Optional string name for hte units of the axis."""


@runtime_checkable
class CoordinateSpace(Protocol):
    """A coordinate space for spatial data.

    Args:
        axes: The axes of the coordinate system in order.

    Lifecycle: experimental
    """

    def __len__(self) -> int: ...

    def __getitem__(self, index: int) -> Axis:  # type: ignore[override]
        ...

    @property
    def axes(self) -> tuple[Axis, ...]:
        """The axes of the coordinate space in order.

        Lifecycle: experimental
        """
        ...

    @property
    def axis_names(self) -> tuple[str, ...]:
        """The names of the axes in order.

        Lifecycle: experimental
        """
        ...


@runtime_checkable
class CoordinateTransform(Protocol):
    """A coordinate transformation from one coordinate space to another.

    Args:
        input_axes: The names of the axes for the input coordinate space.
        output_axes: The names of the axes for the output coordinate space.

    CoordinateTransform classes are composable using the ``@`` (__matmul__) operator.

    Lifecycle: experimental
    """

    def __matmul__(self, other: object) -> "CoordinateTransform": ...

    def inverse_transform(self) -> "CoordinateTransform":
        """Returns the inverse coordinate transform.

        Lifecycle: experimental
        """
        ...

    @property
    def input_axes(self) -> tuple[str, ...]:
        """The names of the axes of the input coordinate space.

        Lifecycle: experimental
        """
        ...

    @property
    def output_axes(self) -> tuple[str, ...]:
        """The names of the axes of the output coordinate space.

        Lifecycle: experimental
        """
        ...
