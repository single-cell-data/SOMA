from typing import MutableMapping, Optional, TypeVar

from typing_extensions import Final

from . import _mixin
from . import base
from . import collection
from . import data
from . import measurement
from . import query

_Self = TypeVar("_Self", bound="Experiment")
_ST = TypeVar("_ST", bound=base.SOMAObject)


class Experiment(MutableMapping[str, _ST]):
    """Mixin for Experiment types."""

    # This class is implemented as a mixin to be used with SOMA classes:
    #
    #     # in a SOMA implementation:
    #     class Experiment(somacore.Experiment, ImplsBaseCollection):
    #         pass
    #
    # Experiment should always appear *first* in the base class list.
    # MutableMapping is listed as the parent type instead of Collection here
    # to avoid the interpreter being unable to pick the right base class:
    #
    #     TypeError: multiple bases have instance lay-out conflict

    __slots__ = ()
    soma_type: Final = "SOMAExperiment"

    obs = _mixin.item(data.DataFrame)
    """Primary observations on the observation axis.

    The contents of the ``soma_joinid`` pseudo-column define the observation
    index domain, i.e. ``obsid``. All observations for the experiment must be
    defined here.
    """

    ms = _mixin.item(
        collection.Collection[measurement.Measurement]  # type: ignore[type-var]
    )
    """A collection of named measurements."""

    def axis_query(
        self: _Self,
        measurement_name: str,
        *,
        obs_query: Optional[query.AxisQuery] = None,
        var_query: Optional[query.AxisQuery] = None,
    ) -> "query.ExperimentAxisQuery[_Self]":
        """Creates an axis query over this experiment.

        See :class:`query.ExperimentAxisQuery` for details on usage.
        """
        # mypy doesn't quite understand descriptors so it issues a spurious
        # error here.
        return query.ExperimentAxisQuery(  # type: ignore[type-var]
            self,
            measurement_name,
            obs_query=obs_query or query.AxisQuery(),
            var_query=var_query or query.AxisQuery(),
        )


class SimpleExperiment(Experiment, collection.SimpleCollection):  # type: ignore[misc]
    """An in-memory Collection with Experiment semantics."""
