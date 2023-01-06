"""Implementations of the composed SOMA data types."""

from typing_extensions import Final

from somacore import _wrap
from somacore import base
from somacore import data


class Measurement(_wrap.CollectionProxy):
    """A set of annotated variables and values for a single measurement."""

    __slots__ = ()

    var = _wrap.item(data.DataFrame)
    """Primary annotations on the variable axis for vars on this meansurement.

    This annotates _columns_ of the ``X`` arrays. The contents of the
    ``soma_joinid`` pseudo-column define the variable index domain (``varid``)
    All variables for this measurement _must_ be defined in this dataframe.
    """

    X = _wrap.item(base.Collection[data.NDArray])
    """A collection of matrices containing feature values.

    Each matrix is indexed by ``[obsid, varid]``. Sparse and dense 2D arrays may
    both be used in any combination in ``X``.
    """

    obsm = _wrap.item(base.Collection[data.DenseNDArray])
    """Matrices containing annotations of each ``obs`` row.

    This has the same shape as ``obs`` and is indexed with ``obsid``.
    """

    obsp = _wrap.item(base.Collection[data.SparseNDArray])
    """Matrices containg pairwise annotations of each ``obs`` row.

    This is indexed by ``[obsid_1, obsid_2]``.
    """

    varm = _wrap.item(base.Collection[data.DenseNDArray])
    """Matrices containing annotations of each ``var`` row.

    This has the same shape as ``var`` and is indexed with ``varid``.
    """

    varp = _wrap.item(base.Collection[data.SparseNDArray])
    """Matrices containg pairwise annotations of each ``var`` row.

    This is indexed by ``[varid_1, varid_2]``.
    """

    soma_type: Final = "SOMAMeasurement"
