"""Implementations of the composed SOMA data types."""

from typing_extensions import Protocol, runtime_checkable

from . import base
from . import collection
from . import data


@runtime_checkable
class Measurement(collection.BaseCollection[base.SOMAObject], Protocol):
    """A set of observations defined by a dataframe, with measurements.

    This is a common set of annotated variables (defined by the ``var``
    dataframe) for which values (e.g., measurements or calculations) are stored
    in sparse and dense ND arrays.

    The observables are inherited from the parent ``Experiment``'s
    ``obs`` dataframe. The ``soma_joinid`` of these observables (``obsid``),
    along with those of the measurement's ``var`` dataframe (``varid``),
    are the indices for all the other matrices stored in the measurement.

    Lifecycle: maturing
    """

    @property
    def var(self) -> data.DataFrame:
        """Primary annotations on the variable axis for vars on this measurement.

        This annotates _columns_ of the ``X`` arrays. The contents of the
        ``soma_joinid`` pseudo-column define the variable index domain (``varid``).
        All variables for this measurement _must_ be defined in this dataframe.

        Lifecycle: maturing
        """
        ...

    @property
    def X(self) -> collection.Collection:
        """A collection of matrices containing feature values.

        Each matrix is indexed by ``[obsid, varid]``. Sparse and dense 2D arrays may
        both be used in any combination in ``X``.

        Lifecycle: maturing
        """
        ...

    @property
    def obsm(self) -> collection.Collection:
        """Matrices containing annotations of each ``obs`` row.

        This has the same shape as ``obs`` and is indexed with ``obsid``.

        Lifecycle: maturing
        """
        ...

    @property
    def obsp(self) -> collection.Collection:
        """Matrices containing pairwise annotations of each ``obs`` row.

        This is indexed by ``[obsid_1, obsid_2]``.
        """
        ...

    @property
    def varm(self) -> collection.Collection:
        """Matrices containing annotations of each ``var`` row.

        This has the same shape as ``var`` and is indexed with ``varid``.

        Lifecycle: maturing
        """
        ...

    @property
    def varp(self) -> collection.Collection:
        """Matrices containing pairwise annotations of each ``var`` row.

        This is indexed by ``[varid_1, varid_2]``.

        Lifecycle: maturing
        """
        ...

    @property
    def var_spatial_presence(self) -> data.DataFrame:
        """A dataframe that stores the presence of var in the spatial scenes.

        This provides a join table for the var ``soma_joinid`` and the scene names used in
        the ``spatial`` collection. This dataframe must contain index columns ``soma_joinid``
        and ``scene_id``. The ``scene_id`` column  must have type ``string``. The
        dataframe must contain a ``boolean`` column ``data``. The values of ``data`` are
        ``True`` if the var with varid ``soma_joinid`` is contained in scene with name
        ``scene_id`` and ``False`` otherwise.

        Lifecycle: experimental
        """
        ...
