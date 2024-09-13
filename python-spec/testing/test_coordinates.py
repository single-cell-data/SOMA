import numpy as np
import pytest

from somacore import AffineTransform
from somacore import CoordinateTransform
from somacore import IdentityTransform
from somacore import ScaleTransform


def check_transform_is_equal(
    actual: CoordinateTransform, desired: CoordinateTransform
) -> None:
    assert actual.input_axes == desired.input_axes
    assert actual.output_axes == desired.output_axes
    if isinstance(desired, IdentityTransform):
        assert isinstance(actual, IdentityTransform)
    elif isinstance(desired, ScaleTransform):
        assert isinstance(actual, ScaleTransform)
        assert desired.isotropic == actual.isotropic
        if desired.isotropic:
            assert actual.scale == desired.scale
        else:
            np.testing.assert_array_equal(actual.scale_factors, desired.scale_factors)
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
        ),
        (
            AffineTransform(
                ["x1", "y1"],
                ["x2", "y2"],
                [[2, 2], [0, 3]],
            ),
            np.array([[2, 2, 0], [0, 3, 0], [0, 0, 1]], np.float64),
        ),
        (
            AffineTransform(
                ["x1", "y1"],
                ["x2", "y2"],
                [[2, 2, 0], [0, 3, 1], [0, 0, 1]],
            ),
            np.array([[2, 2, 0], [0, 3, 1], [0, 0, 1]], np.float64),
        ),
    ],
)
def test_affine_augmented_matrix(input, expected):
    result = input.augmented_matrix
    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize(
    ("input_matrix",), [([1, 2, 3],), ([[1, 0, 1], [0, 1, 1], [1, 0, 1]],)]
)
def test_affine_matrix_value_error(input_matrix):
    with pytest.raises(ValueError):
        AffineTransform(("x1", "y1"), ("x2", "y2"), input_matrix)


@pytest.mark.parametrize(
    ("input_scale_factors", "expected_scale_factors"),
    [
        (1.5, np.array([1.5, 1.5], dtype=np.float64)),
        ([1.5], np.array([1.5, 1.5], dtype=np.float64)),
        ([1, 2], np.array([1.0, 2.0], dtype=np.float64)),
        (np.array([[1, 2]]), np.array([1.0, 2.0], dtype=np.float64)),
    ],
)
def test_scale_factors(input_scale_factors, expected_scale_factors):
    transform = ScaleTransform(("x1", "y1"), ("x2", "y2"), input_scale_factors)


@pytest.mark.parametrize(
    ("input_scale_factors", "expected_scale"),
    [(2, 2.0), (1.4, 1.4), (np.array([2]), 2.0), ([2], 2.0), ([2, 2], 2.0)],
)
def test_isotropic(input_scale_factors, expected_scale):
    transform = ScaleTransform(("x1", "y1"), ("x2", "y2"), input_scale_factors)

    if expected_scale is None:
        assert not transform.isotropic
        with pytest.raises(RuntimeError):
            transform.scale
    else:
        assert transform.isotropic
        assert transform.scale == expected_scale


def test_bad_number_of_scale_factors():
    with pytest.raises(ValueError):
        transform = ScaleTransform(("x1", "y1"), ("x2", "y2"), [1, 2, 3])


@pytest.mark.parametrize(
    ("input", "expected"),
    [
        (
            AffineTransform(
                ["x1", "y1"],
                ["x2", "y2"],
                [[1, 0, 0], [0, 1, 0]],
            ),
            AffineTransform(
                ["x2", "y2"],
                ["x1", "y1"],
                [[1, 0, 0], [0, 1, 0]],
            ),
        ),
        (
            AffineTransform(
                ["x1", "y1"],
                ["x2", "y2"],
                [[1, 0, 5], [0, 1, 10]],
            ),
            AffineTransform(
                ["x2", "y2"],
                ["x1", "y1"],
                [[1, 0, -5], [0, 1, -10]],
            ),
        ),
        (
            AffineTransform(
                ["x1", "y1"],
                ["x2", "y2"],
                [[2, 0, -5], [0, 4, 5]],
            ),
            AffineTransform(
                ["x2", "y2"],
                ["x1", "y1"],
                [[0.5, 0, 2.5], [0, 0.25, -1.25]],
            ),
        ),
        (
            ScaleTransform(["x1", "y1"], ["x2", "y2"], [4, 0.1]),
            ScaleTransform(["x2", "y2"], ["x1", "y1"], [0.25, 10]),
        ),
        (
            ScaleTransform(["x1", "y1"], ["x2", "y2"], 10),
            ScaleTransform(["x2", "y2"], ["x1", "y1"], 0.1),
        ),
        (
            IdentityTransform(["x1", "y1"], ["x2", "y2"]),
            IdentityTransform(["x2", "y2"], ["x1", "y1"]),
        ),
    ],
)
def test_inverse_transform(input, expected):
    result = input.inverse_transform()
    check_transform_is_equal(result, expected)
    result_matrix = input.augmented_matrix @ result.augmented_matrix
    expected_matrix: np.ndarray = np.identity(result.input_rank + 1, dtype=np.float64)
    np.testing.assert_allclose(result_matrix, expected_matrix)


@pytest.mark.parametrize(
    ("transform_a", "transform_b", "expected"),
    [
        (
            IdentityTransform(["x2", "y2"], ["x3", "y3"]),
            IdentityTransform(["x1", "y1"], ["x2", "y2"]),
            IdentityTransform(["x1", "y1"], ["x3", "y3"]),
        ),
        (
            ScaleTransform(
                ["x2", "y2"], ["x3", "y3"], np.array([1.5, 3.0], dtype=np.float64)
            ),
            IdentityTransform(["x1", "y1"], ["x2", "y2"]),
            ScaleTransform(
                ["x1", "y1"], ["x3", "y3"], np.array([1.5, 3.0], dtype=np.float64)
            ),
        ),
        (
            AffineTransform(
                ["x2", "y2"],
                ["x3", "y3"],
                np.array([[1.5, 3.0, 0.0], [-1.5, 3.0, 1.0]], dtype=np.float64),
            ),
            IdentityTransform(["x1", "y1"], ["x2", "y2"]),
            AffineTransform(
                ["x1", "y1"],
                ["x3", "y3"],
                np.array([[1.5, 3.0, 0.0], [-1.5, 3.0, 1.0]], dtype=np.float64),
            ),
        ),
        (
            IdentityTransform(["x2", "y2"], ["x3", "y3"]),
            ScaleTransform(
                ["x1", "y1"], ["x2", "y2"], np.array([1.5, 3.0], dtype=np.float64)
            ),
            ScaleTransform(
                ["x1", "y1"], ["x3", "y3"], np.array([1.5, 3.0], dtype=np.float64)
            ),
        ),
        (
            IdentityTransform(["x2", "y2"], ["x3", "y3"]),
            AffineTransform(
                ["x1", "y1"],
                ["x2", "y2"],
                np.array([[1.5, 3.0, 0.0], [-1.5, 3.0, 1.0]], dtype=np.float64),
            ),
            AffineTransform(
                ["x1", "y1"],
                ["x3", "y3"],
                np.array([[1.5, 3.0, 0.0], [-1.5, 3.0, 1.0]], dtype=np.float64),
            ),
        ),
        (
            ScaleTransform(["x2", "y2"], ["x3", "y3"], [1.0, -1.0]),
            ScaleTransform(["x1", "y1"], ["x2", "y2"], 1.5),
            ScaleTransform(["x1", "y1"], ["x3", "y3"], [1.5, -1.5]),
        ),
        (
            AffineTransform(
                ["x2", "y2"],
                ["x3", "y3"],
                np.array([[2.0, 0.0, 1.0], [0.0, 4.0, 1.0]], dtype=np.float64),
            ),
            AffineTransform(
                ["x1", "y1"],
                ["x2", "y2"],
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
    result = transform_a @ transform_b
    check_transform_is_equal(result, expected)
