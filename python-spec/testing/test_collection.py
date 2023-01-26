import unittest
from typing import Any

from somacore import collection
from somacore import experiment
from somacore import measurement


class SimpleCollectionTest(unittest.TestCase):
    def test_basic(self):
        # Since the SimpleCollection implementation is straightforward this is
        # just to ensure that we actually fulfill everything.

        coll = collection.SimpleCollection[Any]()
        entry_a = collection.SimpleCollection[Any]()
        coll["a"] = entry_a
        self.assertIs(entry_a, coll["a"])
        del coll["a"]

        md = coll.metadata

        md["hello"] = "world"

        self.assertEqual("world", coll.metadata["hello"])

    def test_method_resolution_order(self):
        # Ensures that constant definitions interact correctly with the MRO.

        m = measurement.SimpleMeasurement()
        self.assertEqual("SOMAMeasurement", m.soma_type)
        exp = experiment.SimpleExperiment()
        self.assertEqual("SOMAExperiment", exp.soma_type)
