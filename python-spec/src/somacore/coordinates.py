"""Definitions of types related to coordinate systems."""

import abc
import collections.abc
from dataclasses import dataclass
from typing import Any, Optional, Sequence, Tuple, Union

import numpy as np
import numpy.typing as npt


@dataclass
class Axis(metaclass=abc.ABCMeta):
    """A description of an axis of a coordinate system

    Args:
        name: Name of the axis.
        unit: Optional string units. Defaults to ``None``.
        scale: Optional scale for units. Defaults to ``None``.

    Lifecycle: experimental
    """

    name: str
    units: Optional[str] = None
    scale: Optional[np.float64] = None


class CoordinateSpace(collections.abc.Sequence):
    """A coordinate space for spatial data.

    Args:
        axes: The axes of the coordinate system in order.

    Lifecycle: experimental
    """

    def __init__(self, axes: Sequence[Axis]):
        self._axes = tuple(axes)
        if len(self._axes) == 0:
            raise ValueError("Coordinate space must have at least one axis.")
        if len(set(axis.name for axis in self._axes)) != len(axes):
            raise ValueError("The names for the axes must be unique.")

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
        """The axes in the coordinate space.

        Lifecycle: experimental
        """
        return self._axes

    @property
    def axis_names(self) -> Tuple[str, ...]:
        """The names of the axes in order.

        Lifecycle: experimental
        """
        return tuple(axis.name for axis in self._axes)

    def rank(self) -> int:
        """The number of axes in this coordinate space.

        Lifecycle: experimental
        """
        return len(self)


class CoordinateTransform(metaclass=abc.ABCMeta):
    """A coordinate transformation from one coordinate space to another.

    Args:
        input_axes: The names of the axes for the input coordinate space.
        output_axes: The names of the axes for the output coordinate space.

    Lifecycle: experimental
    """

    def __init__(
        self,
        input_axes: Union[str, Sequence[str]],
        output_axes: Union[str, Sequence[str]],
    ):
        self._input_axes = (
            (input_axes,) if isinstance(input_axes, str) else tuple(input_axes)
        )
        self._output_axes = (
            (output_axes,) if isinstance(output_axes, str) else tuple(output_axes)
        )

    @abc.abstractmethod
    def __matmul__(self, other: Any) -> "CoordinateTransform":
        raise NotImplementedError()

    @abc.abstractmethod
    def __rmatmul__(self, other: Any) -> "CoordinateTransform":
        raise NotImplementedError()

    @abc.abstractmethod
    def inverse_transform(self) -> "CoordinateTransform":
        """Returns the inverse coordinate transform.

        Lifecycle: experimental
        """
        raise NotImplementedError()

    @property
    def input_axes(self) -> Tuple[str, ...]:
        """The names of the axes of the input coordinate space.

        Lifecycle: experimental
        """
        return self._input_axes

    @property
    def input_rank(self) -> int:
        """The number of axes in the input coordinate space.

        Lifecycle: experimental
        """
        return len(self._input_axes)

    @property
    def output_axes(self) -> Tuple[str, ...]:
        """The names of the axes of the output coordinate space.

        Lifecycle: experimental
        """
        return self._output_axes

    @property
    def output_rank(self) -> int:
        """The number of axes in the output coordinate space.

        Lifecycle: experimental
        """
        return len(self._output_axes)


class AffineTransform(CoordinateTransform):
    """An affine coordinate trasformation from one coordinate space to another.

    An affine transform is a combination of a linear transformation and a translation.

    Args:
        input_axes: The names of the axes for the input coordinate space.
        output_axes: The names of the axes for the output coordinate space.
        matrix: Matrix (perhaps augmented) that represents the affine transformation.
            Can be provided as just the linear transform (if no translation), the
            full augmented matrix, or the augmented matrix without the final row.

    Lifecycle: experimental
    """

    def __init__(
        self,
        input_axes: Union[str, Sequence[str]],
        output_axes: Union[str, Sequence[str]],
        matrix: npt.ArrayLike,
    ):
        super().__init__(input_axes, output_axes)

        # Check the rank of the input/output axes match.
        if self.input_rank != self.output_rank:
            raise ValueError(
                "The input axes and output axes must be the same length for an "
                "affine transform."
            )
        rank = self.input_rank

        # Create and validate the augmented matrix.
        self._matrix: npt.NDArray[np.float64] = np.array(matrix, dtype=np.float64)
        if self._matrix.shape == (rank + 1, rank + 1):
            if not (
                self._matrix[-1, -1] == 1.0
                and np.array_equal(self._matrix[-1, :-1], np.zeros((rank,)))
            ):
                raise ValueError(
                    f"Input matrix {self._matrix} has augmented matrix shape, but is not a valid "
                    f"augmented matrix."
                )
        elif self._matrix.shape == (rank, rank + 1):
            self._matrix = np.vstack(
                (
                    self._matrix,
                    np.hstack((np.zeros((rank,)), np.array([1]))),
                )
            )
        elif self._matrix.shape == (rank, rank):
            self._matrix = np.vstack(
                (
                    np.hstack((self._matrix, np.zeros((rank, 1)))),
                    np.hstack((np.zeros((rank,)), np.array([1]))),
                )
            )
        else:
            raise ValueError(
                f"Unexpected shape {self._matrix.shape} for the input affine matrix."
            )

    def __matmul__(self, other: Any) -> CoordinateTransform:
        if isinstance(other, CoordinateTransform):
            if self.input_axes != other.output_axes:
                raise ValueError("Axis mismatch between transformations.")
            if isinstance(other, IdentityTransform):
                return AffineTransform(other.input_axes, self.output_axes, self._matrix)
            if isinstance(other, AffineTransform):
                return AffineTransform(
                    other.input_axes,
                    self.output_axes,
                    self.augmented_matrix @ other.augmented_matrix,
                )
        if isinstance(other, np.ndarray):
            raise NotImplementedError(
                "Support for multiplying by numpy arrays is not yet implemented."
            )
        raise TypeError(
            f"Cannot multiply a CoordinateTransform by type {type(other)!r}."
        )

    def __rmatmul__(self, other: Any) -> CoordinateTransform:
        if isinstance(other, CoordinateTransform):
            if other.input_axes != self.output_axes:
                raise ValueError("Axis mismatch between transformations.")
            if isinstance(other, IdentityTransform):
                return AffineTransform(
                    self.input_axes, other.output_axes, self.augmented_matrix
                )
            if isinstance(other, AffineTransform):
                return AffineTransform(
                    self.input_axes,
                    other.output_axes,
                    other.augmented_matrix @ self.augmented_matrix,
                )
        if isinstance(other, np.ndarray):
            raise NotImplementedError(
                "Support for multiplying by numpy arrays is not yet implemented."
            )
        raise TypeError(
            f"Cannot multiply a CoordinateTransform by type {type(other)!r}."
        )

    @property
    def augmented_matrix(self) -> npt.NDArray[np.float64]:
        """Returns the augmented affine matrix for the transformation.

        Lifecycle: experimental
        """
        return self._matrix

    def inverse_transform(self) -> CoordinateTransform:
        """Returns the inverse coordinate transform.

        Lifecycle: experimental
        """
        inv_a = np.linalg.inv(self._matrix[:-1, :-1])
        b2 = -inv_a @ self._matrix[:-1, -1].reshape((self.output_rank, 1))
        inv_augmented: npt.NDArray[np.float64] = np.vstack(
            (
                np.hstack((inv_a, b2)),
                np.hstack((np.zeros(self.output_rank), np.array([1]))),
            )
        )
        return AffineTransform(self.output_axes, self.input_axes, inv_augmented)


class ScaleTransform(AffineTransform):
    """A scale coordinate transformation from one coordinate space to another.

    Args:
        input_axes: The names of the axes for the input coordinate space.
        output_axes: The names of the axes for the output coordinate space.
        scale_factors: The scale factors for the transformation. May be a single
            value for isotropic (uniform) scale transformations or a value per axis
            for non-isotropic transformations.

    Lifecycle: experimental
    """

    def __init__(
        self,
        input_axes: Union[str, Sequence[str]],
        output_axes: Union[str, Sequence[str]],
        scale_factors: npt.ArrayLike,
    ):
        super(AffineTransform, self).__init__(input_axes, output_axes)
        if self.input_rank != self.output_rank:
            raise ValueError("Incompatible rank of input and output axes")

        self._scale_factors: Union[np.float64, npt.NDArray[np.float64]] = np.array(
            scale_factors, dtype=np.float64
        )
        if self._scale_factors.size == 1:
            self._scale_factors = self._scale_factors.reshape((1,))[0]
            self._isotropic = True
        elif self._scale_factors.size == self.input_rank:
            self._scale_factors = self._scale_factors.reshape((self.input_rank,))
            if np.all(self._scale_factors == self._scale_factors[0]):
                self._scale_factors = self._scale_factors[0]
                self._isotropic = True
            else:
                self._isotropic = False
        else:
            raise ValueError(
                f"Scale factors have unexpected shape={self._scale_factors.shape} "
                f"for a transform with rank={self.input_rank}."
            )

    def __matmul__(self, other: Any) -> CoordinateTransform:
        if isinstance(other, CoordinateTransform):
            if self.input_axes != other.output_axes:
                raise ValueError("Axis mismatch between transformations.")
            if isinstance(other, ScaleTransform):  # Includes IdentityTransform
                return ScaleTransform(
                    other.input_axes,
                    self.output_axes,
                    self.scale_factors * other.scale_factors,
                )
            if isinstance(other, AffineTransform):
                return AffineTransform(
                    other.input_axes,
                    self.output_axes,
                    self.augmented_matrix.__matmul__(other.augmented_matrix),
                )
        if isinstance(other, np.ndarray):
            raise NotImplementedError(
                "Support for multiplying by numpy arrays is not yet implemented."
            )
        raise TypeError(
            f"Cannot multiply a CoordinateTransform by type {type(other)!r}."
        )

    def __rmatmul__(self, other: Any) -> CoordinateTransform:
        if isinstance(other, CoordinateTransform):
            if other.input_axes != self.output_axes:
                raise ValueError("Axis mismatch between transformations.")
            if isinstance(other, IdentityTransform):
                return ScaleTransform(
                    self.input_axes, other.output_axes, self._scale_factors
                )
            if isinstance(other, ScaleTransform):
                return ScaleTransform(
                    self.input_axes,
                    other.output_axes,
                    self._scale_factors * other._scale_factors,
                )
            if isinstance(other, AffineTransform):
                return AffineTransform(
                    self.input_axes,
                    other.output_axes,
                    other.augmented_matrix.__matmul__(self.augmented_matrix),
                )
        if isinstance(other, np.ndarray):
            raise NotImplementedError(
                "Support for multiplying by numpy arrays is not yet implemented."
            )
        raise TypeError(
            f"Cannot multiply a CoordinateTransform by type {type(other)!r}."
        )

    @property
    def augmented_matrix(self) -> npt.NDArray[np.float64]:
        """Returns the augmented affine matrix for the transformation.

        Lifecycle: experimental
        """
        scales = np.append(self.scale_factors, [1.0])
        return np.diag(scales)

    def inverse_transform(self) -> CoordinateTransform:
        """Returns the inverse coordinate transform.

        Lifecycle: experimental
        """
        return ScaleTransform(
            self.output_axes, self.input_axes, 1.0 / self._scale_factors
        )

    @property
    def isotropic(self) -> bool:
        """Returns ``True`` if this is an isotropic (uniform) scale transform.

        Lifecycle: experimental
        """
        return self._isotropic

    @property
    def scale(self) -> np.float64:
        """Returns the scale factor for an isotropic (uniform) scale transform.

        Raises:
            RuntimeError: If scale transform is not isotropic.

        Lifecycle: experimental
        """
        if not self._isotropic:
            raise RuntimeError(
                "Scale transform is not isotropic. Cannot get a single scale."
            )
        assert isinstance(self._scale_factors, np.float64)
        return self._scale_factors

    @property
    def scale_factors(self) -> npt.NDArray[np.float64]:
        """Returns the scale factors as an one-dimensional numpy array.

        Lifecycle: experimental
        """
        if self._isotropic:
            assert isinstance(self._scale_factors, np.float64)
            return np.array(self.input_rank * [self._scale_factors], dtype=np.float64)
        assert isinstance(self._scale_factors, np.ndarray)
        return self._scale_factors


class IdentityTransform(ScaleTransform):
    """The identify transform from one coordinate space to another.

    This transform only changes the name of the axes.

    Args:
        input_axes: The names of the axes for the input coordinate space.
        output_axes: The names of the axes for the output coordinate space.

    Lifecycle: experimental
    """

    def __init__(
        self,
        input_axes: Union[str, Sequence[str]],
        output_axes: Union[str, Sequence[str]],
    ):
        super(AffineTransform, self).__init__(input_axes, output_axes)
        if self.input_rank != self.output_rank:
            raise ValueError("Incompatible rank of input and output axes")

    def __matmul__(self, other: Any) -> CoordinateTransform:
        if isinstance(other, CoordinateTransform):
            if isinstance(other, IdentityTransform):
                if other.output_axes != self.input_axes:
                    raise ValueError("Axis mismatch between transformations.")
                return IdentityTransform(other.input_axes, self.output_axes)
            return other.__rmatmul__(self)
        if isinstance(other, np.ndarray):
            raise NotImplementedError(
                "Support for multiplying by numpy arrays is not yet implemented."
            )
        raise TypeError(
            f"Cannot multiply a CoordinateTransform by type {type(other)!r}."
        )

    def __rmatmul__(self, other: Any) -> CoordinateTransform:
        if isinstance(other, CoordinateTransform):
            if isinstance(other, IdentityTransform):
                if other.output_axes != self.input_axes:
                    raise ValueError("Axis mismatch between transformations.")
                return IdentityTransform(self.input_axes, other.output_axes)
            return other.__matmul__(self)
        if isinstance(other, np.ndarray):
            raise NotImplementedError(
                "Support for multiplying by numpy arrays is not yet implemented."
            )
        raise TypeError(
            f"Cannot multiply a CoordinateTransform by type {type(other)!r}."
        )

    @property
    def augmented_matrix(self) -> npt.NDArray[np.float64]:
        """Returns the augmented affine matrix for the transformation.

        Lifecycle: experimental
        """
        return np.identity(self.input_rank + 1)

    def inverse_transform(self) -> CoordinateTransform:
        """Returns the inverse coordinate transform.

        Lifecycle: experimental
        """
        return IdentityTransform(self.output_axes, self.input_axes)

    @property
    def isotropic(self) -> bool:
        """Returns ``True`` if this is an isotropic (uniform) scale transform.

        Lifecycle: experimental
        """
        return True

    @property
    def scale(self) -> np.float64:
        """Returns the scale factor for an isotropic (uniform) scale transform.

        This will always return 1.

        Lifecycle: experimental
        """
        return np.float64(1)

    @property
    def scale_factors(self) -> npt.NDArray[np.float64]:
        """Returns the scale factors as an one-dimensional numpy array.

        This will always be a vector of ones.

        Lifecycle: experimental

        """
        return np.array(self.input_rank * [1.0], dtype=np.float64)
