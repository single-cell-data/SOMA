from __future__ import annotations

from typing import runtime_checkable

from typing_extensions import Protocol

from . import base
from . import collection
from . import data
from . import query
from .query import ExperimentAxisQuery


@runtime_checkable
class Experiment(collection.BaseCollection[base.SOMAObject], Protocol):
    """A collection subtype representing an annotated 2D matrix of measurements.

    In single cell biology, this can represent multiple modes of measurement
    across a single collection of cells (i.e., a "multimodal dataset").
    Within an experiment, a set of measurements on a single set of variables
    (i.e., features) is represented as a :class:`~measurement.Measurement`.

    Lifecycle: maturing
    """

    @property
    def obs(self) -> data.DataFrame:
        """Primary observations on the observation axis.

        The contents of the ``soma_joinid`` pseudo-column define the observation index domain, i.e. ``obsid``. All
        observations for the experiment must be defined here.

        Lifecycle: maturing
        """
        ...

    @property
    def ms(self) -> collection.Collection:
        """A collection of named measurements.

        Lifecycle: maturing
        """
        ...

    @property
    def spatial(self) -> collection.Collection:
        """A collection of named spatial scenes.

        Lifecycle: experimental
        """
        ...

    @property
    def obs_spatial_presence(self) -> data.DataFrame:
        """A dataframe that stores the presence of obs in the spatial scenes.

        This provides a join table for the obs ``soma_joinid`` and the scene names used in
        the ``spatial`` collection. This dataframe must contain index columns ``soma_joinid``
        and ``scene_id``. The ``scene_id`` column must have type ``string``. The
        dataframe must contain a ``boolean`` column ``soma_data``. The values of ``soma_data`` are
        ``True`` if the obs ``soma_joinid`` is contained in the scene
        ``scene_id`` and ``False`` otherwise.

        Lifecycle: experimental
        """
        ...

    def axis_query(
        self,
        measurement_name: str,
        *,
        var_query: query.AxisQuery | None = None,
        obs_query: query.AxisQuery | None = None,
    ) -> ExperimentAxisQuery:
        """Creates an axis query over this experiment.

        See :class:`query.ExperimentAxisQuery` for details on usage.

        Lifecycle: maturing
        """
        ...
