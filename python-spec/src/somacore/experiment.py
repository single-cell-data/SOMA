from typing import TypeVar

from typing_extensions import Final

from . import _wrap
from . import collection
from . import data
from . import measurement
from . import query

_Self = TypeVar("_Self", bound="Experiment")


class Experiment(_wrap.CollectionProxy):
    """A set of observations defined by a DataFrame, with measurements."""

    obs = _wrap.item(data.DataFrame)
    """Primary observations on the observation axis.

    The contents of the ``soma_joinid`` pseudo-column define the observation
    index domain, i.e. ``obsid``. All observations for the experiment must be
    defined here.
    """

    ms = _wrap.item(collection.Collection[measurement.Measurement])
    """A collection of named measurements."""

    def axis_query(
        self: _Self,
        measurement_name: str,
        *,
        obs_query: query.AxisQuery = query.AxisQuery(),
        var_query: query.AxisQuery = query.AxisQuery(),
    ) -> "query.ExperimentAxisQuery[_Self]":
        """Creates an axis query over this experiment.

        See :class:`query.ExperimentAxisQuery` for details on usage.
        """
        # mypy doesn't quite understand descriptors so it issues a spurious
        # error here.
        return query.ExperimentAxisQuery(  # type: ignore[type-var]
            self, measurement_name, obs_query=obs_query, var_query=var_query
        )

    soma_type: Final = "SOMAExperiment"
