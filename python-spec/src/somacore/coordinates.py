"""Definitions of types related to coordinate systems."""

import abc
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Optional, Tuple, Union

import numpy as np
import pyarrow as pa


@dataclass
class Axis(metaclass=abc.ABCMeta):
    """A description of an axis of a coordinate system

    Args:
        name: Name of the axis.
        unit:

    Lifecycle: experimental
    """

    name: str
    units: Optional[str] = None
    scale: Optional[np.float64] = None


class CoordinateSpace(Sequence[Axis]):
    """A coordinate system for spatial data."""

    def __init__(self, axes: Sequence[Axis]):
        """TODO: Add docstring"""
        # TODO: Needs good, comprehensive error handling.
        if len(tuple(axes)) == 0:
            raise ValueError("Coordinate space must have at least one axis.")
        self._axes = tuple(axes)

    def __len__(self) -> int:
        return len(self._axes)

    def __getitem__(self, index: int) -> Axis:  # type: ignore[override]
        return self._axes[index]

    def __repr__(self) -> str:
        output = f"<{type(self).__name__}\n"
        for axis in self._axes:
            output += f"  {axis},\n"
        return output + ">"

    @property
    def axes(self) -> Tuple[Axis, ...]:
        """TODO: Add docstring"""
        return self._axes

    @property
    def axis_names(self) -> Tuple[str, ...]:
        return tuple(axis.name for axis in self._axes)

    def rank(self) -> int:
        return len(self)


class CoordinateTransform(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def input_axes(self) -> Tuple[str, ...]:
        """TODO: Add docstring for input_space"""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def output_axes(self) -> Tuple[str, ...]:
        """TODO: Add docstring for output_space"""
        raise NotImplementedError()

    # TODO: Switch to be overloaded instead of using Union
    @abc.abstractmethod
    def apply(self, data: Union[pa.Tensor, pa.Table]) -> Union[pa.Tensor, pa.Table]:
        """TODO: Add docstring for apply"""
        raise NotImplementedError()
