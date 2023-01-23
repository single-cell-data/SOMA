import unittest

from somacore import collection


class SimpleCollectionTest(unittest.TestCase):
    def test_basic(self):
        # Since the SimpleCollection implementation is straightforward this is
        # just to ensure that we actually fulfill everything.

        coll = collection.SimpleCollection()
        entry_a = collection.SimpleCollection()
        coll["a"] = entry_a
        self.assertIs(entry_a, coll["a"])
        del coll["a"]

        md = coll.metadata

        md["hello"] = "world"

        self.assertEqual("world", coll.metadata["hello"])
