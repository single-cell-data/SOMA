"""Module base for the Python reference specification of SOMA.

Types will be defined in their own modules and then imported here for a single
unified namespace.
"""

from somacore import _version
from somacore import base
from somacore import data
from somacore import ephemeral
from somacore import options

__version__ = _version.version
__version_tuple__ = _version.version_tuple

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
)
