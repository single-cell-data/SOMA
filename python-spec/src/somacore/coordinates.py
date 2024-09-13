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
        unit_name: Optional string name for the units. Defaults to ``None``.
        unit_scale: Optional scale for units. Defaults to ``None``.

    Lifecycle: experimental
    """

    name: str
    unit_name: Optional[str] = None
    unit_scale: Optional[np.float64] = None


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


class CoordinateTransform(metaclass=abc.ABCMeta):
    """A coordinate transformation from one coordinate space to another.

    Args:
        input_axes: The names of the axes for the input coordinate space.
        output_axes: The names of the axes for the output coordinate space.

    CoordinateTransform classes are composable using the ``@`` (__matmul__) operator.

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
    def __matmul__(self, other: "CoordinateTransform") -> "CoordinateTransform":
        raise NotImplementedError()

    @abc.abstractmethod
    def __rmatmul__(self, other: "CoordinateTransform") -> "CoordinateTransform":
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
    def output_axes(self) -> Tuple[str, ...]:
        """The names of the axes of the output coordinate space.

        Lifecycle: experimental
        """
        return self._output_axes


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
        if len(self.input_axes) != len(self.output_axes):
            raise ValueError(
                "The input axes and output axes must be the same length for an "
                "affine transform."
            )
        rank = len(self.input_axes)

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
        raise TypeError(
            f"Cannot multiply a CoordinateTransform by type {type(other)!r}."
        )

    def __rmatmul__(self, other: Any) -> CoordinateTransform:
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
        rank = len(self.output_axes)
        inv_a = np.linalg.inv(self._matrix[:-1, :-1])
        b2 = -inv_a @ self._matrix[:-1, -1].reshape((rank, 1))
        inv_augmented: npt.NDArray[np.float64] = np.vstack(
            (
                np.hstack((inv_a, b2)),
                np.hstack((np.zeros(rank), np.array([1]))),
            )
        )
        return AffineTransform(self.output_axes, self.input_axes, inv_augmented)


class ScaleTransform(AffineTransform):
    """A scale coordinate transformation from one coordinate space to another.

    Args:
        input_axes: The names of the axes for the input coordinate space.
        output_axes: The names of the axes for the output coordinate space.
        scale_factors: The scale factors for the transformation. There must be one
            value per axis.

    Lifecycle: experimental
    """

    def __init__(
        self,
        input_axes: Union[str, Sequence[str]],
        output_axes: Union[str, Sequence[str]],
        scale_factors: npt.ArrayLike,
    ):
        super(AffineTransform, self).__init__(input_axes, output_axes)
        if len(self.input_axes) != len(self.output_axes):
            raise ValueError("Incompatible rank of input and output axes")
        rank = len(self.input_axes)

        self._scale_factors: npt.NDArray[np.float64] = np.array(
            scale_factors, dtype=np.float64
        )
        if self._scale_factors.size != rank:
            raise ValueError(
                f"Scale factors have unexpected shape={self._scale_factors.shape} "
                f"for a transform with rank={rank}."
            )
        self._scale_factors = self._scale_factors.reshape((rank,))

    def __matmul__(self, other: CoordinateTransform) -> CoordinateTransform:
        if self.input_axes != other.output_axes:
            raise ValueError("Axis mismatch between transformations.")
        if isinstance(other, ScaleTransform):
            return ScaleTransform(
                other.input_axes,
                self.output_axes,
                self.scale_factors * other.scale_factors,
            )
        return super().__matmul__(other)

    def __rmatmul__(self, other: CoordinateTransform) -> CoordinateTransform:
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
                self.scale_factors * other.scale_factors,
            )
        return super().__rmatmul__(other)

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
    def scale_factors(self) -> npt.NDArray[np.float64]:
        """Returns the scale factors as an one-dimensional numpy array.

        Lifecycle: experimental
        """
        return self._scale_factors


class UniformScaleTransform(ScaleTransform):
    """A scale coordinate transformation from one coordinate space to another.

    Args:
        input_axes: The names of the axes for the input coordinate space.
        output_axes: The names of the axes for the output coordinate space.
        scale: The scale factor for all axes.

    Lifecycle: experimental
    """

    def __init__(
        self,
        input_axes: Union[str, Sequence[str]],
        output_axes: Union[str, Sequence[str]],
        scale: Union[int, float, np.float64],
    ):
        super(AffineTransform, self).__init__(input_axes, output_axes)
        if len(self.input_axes) != len(self.output_axes):
            raise ValueError("Incompatible rank of input and output axes")
        self._scale = np.float64(scale)

    def __matmul__(self, other: CoordinateTransform) -> CoordinateTransform:
        if isinstance(other, UniformScaleTransform):
            if self.input_axes != other.output_axes:
                raise ValueError("Axis mismatch between transformations.")
            return UniformScaleTransform(
                other.input_axes, self.output_axes, self.scale * other.scale
            )
        return super().__matmul__(other)

    def __rmatmul__(self, other: CoordinateTransform) -> CoordinateTransform:
        if isinstance(other, IdentityTransform):
            if other.input_axes != self.output_axes:
                raise ValueError("Axis mismatch between transformations.")
                return ScaleTransform(
                    self.input_axes, other.output_axes, self._scale_factors
                )
        return super().__rmatmul__(other)

    def inverse_transform(self) -> CoordinateTransform:
        """Returns the inverse coordinate transform.

        Lifecycle: experimental
        """
        return UniformScaleTransform(
            self.output_axes, self.input_axes, 1.0 / self._scale
        )

    @property
    def scale(self) -> np.float64:
        """Returns the scale factor for the uniform scale transform.

        Lifecycle: experimental
        """
        return self._scale

    @property
    def scale_factors(self) -> npt.NDArray[np.float64]:
        """Returns the scale factors as an one-dimensional numpy array.

        Lifecycle: experimental
        """
        return np.array(len(self.input_axes) * [self._scale], dtype=np.float64)


class IdentityTransform(UniformScaleTransform):
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
        if len(self.input_axes) != len(self.output_axes):
            raise ValueError("Incompatible rank of input and output axes")

    def __matmul__(self, other: CoordinateTransform) -> CoordinateTransform:
        if isinstance(other, IdentityTransform):
            if other.output_axes != self.input_axes:
                raise ValueError("Axis mismatch between transformations.")
            return IdentityTransform(other.input_axes, self.output_axes)
        return other.__rmatmul__(self)

    def __rmatmul__(self, other: CoordinateTransform) -> CoordinateTransform:
        if isinstance(other, IdentityTransform):
            if other.output_axes != self.input_axes:
                raise ValueError("Axis mismatch between transformations.")
            return IdentityTransform(self.input_axes, other.output_axes)
        return other.__matmul__(self)

    @property
    def augmented_matrix(self) -> npt.NDArray[np.float64]:
        """Returns the augmented affine matrix for the transformation.

        Lifecycle: experimental
        """
        return np.identity(len(self.input_axes) + 1)

    def inverse_transform(self) -> CoordinateTransform:
        """Returns the inverse coordinate transform.

        Lifecycle: experimental
        """
        return IdentityTransform(self.output_axes, self.input_axes)

    @property
    def scale(self) -> np.float64:
        """Returns the scale factor for an uniform scale transform.

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
        return np.array(len(self.input_axes) * [1.0], dtype=np.float64)
