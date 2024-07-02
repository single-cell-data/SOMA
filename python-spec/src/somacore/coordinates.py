"""Definitions of types related to coordinate systems."""

import abc
from typing import Optional, Tuple

import numpy as np
import numpy.typing as npt
from typing_extensions import Self


class Axis(metaclass=abc.ABCMeta):
    """A description of an axis of a coordinate system

    Lifecycle: experimental
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """TODO: Add docstring for Axis.name"""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def type(self) -> Optional[str]:
        """TODO: Add docstring for Axis.type"""
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def unit(self) -> Optional[str]:
        """TODO: Add docstring for Axis.unit"""
        raise NotImplementedError()


class CoordinateSystem(metaclass=abc.ABCMeta):
    """A coordinate system for spatial data."""

    @property
    @abc.abstractmethod
    def axes(self) -> Tuple[Axis, ...]:
        """TODO: Add docstring for CoordinateSystem.axes"""
        raise NotImplementedError()


class CoordinateTransform(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def apply(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """A function that transforms an (N, 2) or (N, 3) ndarray of float64
        values according to this coordinate transformation.

        Parameters:
            x: (N, 2) or (N, 3) array of floats to transform.

        Returns:
            The transformed array.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def invert(self) -> Self:
        """Returns the inverse coordinate transformation."""
        raise NotImplementedError()

    @abc.abstractmethod
    def to_numpy(self) -> npt.NDArray[np.float64]:
        """TODO: Add docstring for Transformation.to_numpy"""
        raise NotImplementedError()
