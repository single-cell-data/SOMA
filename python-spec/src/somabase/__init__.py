"""Module base for the Python reference specification of SOMA.

Types will be defined in their own modules and then imported here for a single
unified namespace.
"""

from somabase import base
from somabase import data
from somabase import options

SOMAObject = base.SOMAObject
Collection = base.Collection

DataFrame = data.DataFrame
NDArray = data.NDArray
DenseNDArray = data.DenseNDArray
SparseNDArray = data.SparseNDArray

IOfN = options.IOfN
BatchSize = options.BatchSize

__all__ = (
    "SOMAObject",
    "Collection",
    "DataFrame",
    "NDArray",
    "DenseNDArray",
    "SparseNDArray",
    "IOfN",
    "BatchSize",
)
