"""Implementations of the composed SOMA data types."""

from typing import MutableMapping, TypeVar

from typing_extensions import Final

from . import _mixin
from . import base
from . import collection
from . import data

_ST = TypeVar("_ST", bound=base.SOMAObject)


class Measurement(MutableMapping[str, _ST]):
    """A set of observations defined by a DataFrame, with measurements."""

    # This class is implemented as a mixin to be used with SOMA classes:
    #
    #     # in a SOMA implementation:
    #     class Measurement(somacore.Measurement, ImplBaseCollection):
    #         pass
    #
    # Measurement should always appear *first* in the base class list.
    # MutableMapping is listed as the parent type instead of Collection here
    # to avoid the interpreter being unable to pick the right base class:
    #
    #     TypeError: multiple bases have instance lay-out conflict

    __slots__ = ()
    soma_type: Final = "SOMAMeasurement"

    var = _mixin.item(data.DataFrame)
    """Primary annotations on the variable axis for vars on this meansurement.

    This annotates _columns_ of the ``X`` arrays. The contents of the
    ``soma_joinid`` pseudo-column define the variable index domain (``varid``)
    All variables for this measurement _must_ be defined in this dataframe.
    """

    X = _mixin.item(collection.Collection[data.NDArray])
    """A collection of matrices containing feature values.

    Each matrix is indexed by ``[obsid, varid]``. Sparse and dense 2D arrays may
    both be used in any combination in ``X``.
    """

    obsm = _mixin.item(collection.Collection[data.DenseNDArray])
    """Matrices containing annotations of each ``obs`` row.

    This has the same shape as ``obs`` and is indexed with ``obsid``.
    """

    obsp = _mixin.item(collection.Collection[data.SparseNDArray])
    """Matrices containg pairwise annotations of each ``obs`` row.

    This is indexed by ``[obsid_1, obsid_2]``.
    """

    varm = _mixin.item(collection.Collection[data.DenseNDArray])
    """Matrices containing annotations of each ``var`` row.

    This has the same shape as ``var`` and is indexed with ``varid``.
    """

    varp = _mixin.item(collection.Collection[data.SparseNDArray])
    """Matrices containg pairwise annotations of each ``var`` row.

    This is indexed by ``[varid_1, varid_2]``.
    """


class SimpleMeasurement(Measurement, collection.SimpleCollection):  # type: ignore[misc]
    """An in-memory Collection with Measurement semantics."""
