"""Module base for the Python reference specification of SOMA.

Types will be defined in their own modules and then imported here for a single
unified namespace.
"""

from somabase import base
from somabase import options

SOMAObject = base.SOMAObject
Collection = base.Collection

IOfN = options.IOfN
BatchSize = options.BatchSize
BatchFormat = options.BatchFormat

__all__ = (
    "SOMAObject",
    "Collection",

    "IOfN",
    "BatchSize",
)
