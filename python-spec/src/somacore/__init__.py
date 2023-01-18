"""Module base for the Python reference specification of SOMA.

Types will be defined in their own modules and then imported here for a single
unified namespace.
"""

from typing import Tuple, Union

from somacore import base
from somacore import data
from somacore import ephemeral
from somacore import options
from somacore.query import axis
from somacore.query import query

try:
    # This trips up mypy since it's a generated file:
    from somacore import _version  # type: ignore[attr-defined]

    __version__: str = _version.version
    __version_tuple__: Tuple[Union[int, str], ...] = _version.version_tuple
except ImportError:
    __version__ = "0.0.0.dev+invalid"
    __version_tuple__ = (0, 0, 0, "dev", "invalid")

SOMAObject = base.SOMAObject
Collection = base.Collection

SimpleCollection = ephemeral.SimpleCollection

DataFrame = data.DataFrame
NDArray = data.NDArray
DenseNDArray = data.DenseNDArray
SparseNDArray = data.SparseNDArray
ReadIter = data.ReadIter
SparseRead = data.SparseRead

IOfN = options.IOfN
BatchSize = options.BatchSize
ResultOrder = options.ResultOrder

AxisQuery = axis.AxisQuery
ExperimentAxisQuery = query.ExperimentAxisQuery

__all__ = (
    "SOMAObject",
    "Collection",
    "DataFrame",
    "NDArray",
    "DenseNDArray",
    "SparseNDArray",
    "ReadIter",
    "SparseRead",
    "IOfN",
    "BatchSize",
    "ResultOrder",
    "AxisQuery",
)
