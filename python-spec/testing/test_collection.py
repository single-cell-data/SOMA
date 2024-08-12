import unittest
from typing import Any

from somacore import ephemeral


class EphemeralCollectionTest(unittest.TestCase):
    def test_basic(self):
        # Since the ephemeral Collection implementation is straightforward,
        # this is just to ensure that we actually fulfill everything.

        coll = ephemeral.Collection[Any]()
        entry_a = ephemeral.Collection[Any]()
        coll["a"] = entry_a
        self.assertIs(entry_a, coll["a"])
        del coll["a"]

        md = coll.metadata

        md["hello"] = "world"

        self.assertEqual("world", coll.metadata["hello"])

    def test_equality_identity(self):
        # Ensures that only object identity is used to compare SOMA objects,
        # and nothing else.
        # If these were any other Mapping type, they would be `__eq__` here,
        # since they both have the same (i.e., no) elements.
        coll = ephemeral.Collection[Any]()
        coll_2 = ephemeral.Collection[Any]()
        self.assertNotEqual(coll, coll_2)
        both = frozenset((coll, coll_2))
        self.assertIn(coll, both)
        self.assertIn(coll_2, both)

    def test_method_resolution_order(self):
        # Ensures that constant definitions interact correctly with the MRO.

        m = ephemeral.Measurement()
        self.assertEqual("SOMAMeasurement", m.soma_type)
        exp = ephemeral.Experiment()
        self.assertEqual("SOMAExperiment", exp.soma_type)
        scene = ephemeral.Scene()
        self.assertEqual("SOMAScene", scene.soma_type)
        img = ephemeral.Image2DCollection()
        self.assertEqual("SOMAImage2DCollection", img.soma_type)
