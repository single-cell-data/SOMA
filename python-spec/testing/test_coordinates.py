import numpy as np
import pytest

from somacore import AffineTransform
from somacore import CoordinateTransform
from somacore import IdentityTransform


def check_transform_is_equal(
    actual: CoordinateTransform, desired: CoordinateTransform
) -> None:
    assert actual.input_axes == desired.input_axes
    assert actual.output_axes == desired.output_axes
    if isinstance(desired, IdentityTransform):
        assert isinstance(actual, IdentityTransform)
    elif isinstance(desired, AffineTransform):
        assert isinstance(actual, AffineTransform)
        np.testing.assert_array_equal(actual.augmented_matrix, desired.augmented_matrix)
    else:
        assert False


@pytest.mark.parametrize(
    ("input", "expected"),
    [
        (
            AffineTransform(
                ["x1", "y1"],
                ["x2", "y2"],
                [[2, 2, 0], [0, 3, 1]],
            ),
            np.array([[2, 2, 0], [0, 3, 1], [0, 0, 1]], np.float64),
        )
    ],
)
def test_affine_augmented_matrix(input, expected):
    result = input.augmented_matrix
    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize(
    ("transform_a", "transform_b", "expected"),
    [
        (
            IdentityTransform(["x1", "y1"], ["x2", "y2"]),
            IdentityTransform(["x2", "y2"], ["x3", "y3"]),
            IdentityTransform(["x1", "y1"], ["x3", "y3"]),
        ),
        (
            IdentityTransform(["x1", "y1"], ["x2", "y2"]),
            AffineTransform(
                ["x2", "y2"],
                ["x3", "y3"],
                np.array([[1.5, 3.0, 0.0], [-1.5, 3.0, 1.0]], dtype=np.float64),
            ),
            AffineTransform(
                ["x1", "y1"],
                ["x3", "y3"],
                np.array([[1.5, 3.0, 0.0], [-1.5, 3.0, 1.0]], dtype=np.float64),
            ),
        ),
        (
            AffineTransform(
                ["x1", "y1"],
                ["x2", "y2"],
                np.array([[1.5, 3.0, 0.0], [-1.5, 3.0, 1.0]], dtype=np.float64),
            ),
            IdentityTransform(["x2", "y2"], ["x3", "y3"]),
            AffineTransform(
                ["x1", "y1"],
                ["x3", "y3"],
                np.array([[1.5, 3.0, 0.0], [-1.5, 3.0, 1.0]], dtype=np.float64),
            ),
        ),
        (
            AffineTransform(
                ["x1", "y1"],
                ["x2", "y2"],
                np.array([[2.0, 0.0, 1.0], [0.0, 4.0, 1.0]], dtype=np.float64),
            ),
            AffineTransform(
                ["x2", "y2"],
                ["x3", "y3"],
                np.array([[1.0, 1.0, -1.0], [0.0, 1.0, 2.0]], dtype=np.float64),
            ),
            AffineTransform(
                ["x1", "y1"],
                ["x3", "y3"],
                np.array([[2.0, 2.0, -1.0], [0.0, 4.0, 9.0]], dtype=np.float64),
            ),
        ),
    ],
)
def test_multiply_tranform(
    transform_a,
    transform_b,
    expected: CoordinateTransform,
):
    result = transform_a * transform_b
    check_transform_is_equal(result, expected)
