import unittest

from somacore import _wrap
from somacore import ephemeral


class TestWrapper(unittest.TestCase):
    def test_sanity(self):
        backing = ephemeral.SimpleCollection()
        wrapped = _wrap.CollectionProxy(backing)

        backing_repr = repr(backing)
        self.assertEqual(f"CollectionProxy({backing_repr})", repr(wrapped))

        wrapped["x"] = "y"
        self.assertIn("x", wrapped)
        self.assertEqual(wrapped["x"], "y")
        self.assertEqual(backing["x"], "y")
        self.assertEqual("y", wrapped.get("x", "z"))
        self.assertIsNone(wrapped.get("missing"))
        self.assertEqual("?", wrapped.get("missing", "?"))

        del wrapped["x"]
        self.assertNotIn("x", wrapped)
        self.assertNotIn("x", backing)

        wrapped.update(a="b", c="d", e="f")

        self.assertEqual("ace", "".join(wrapped))
        self.assertEqual({"a", "c", "e"}, set(wrapped.keys()))
        self.assertEqual("bdf", "".join(wrapped.values()))
        self.assertEqual(
            [("a", "b"), ("c", "d"), ("e", "f")],
            list(wrapped.items()),
        )
        self.assertEqual(("a", "b"), wrapped.popitem())
        self.assertEqual(2, len(wrapped))
        self.assertEqual("f", wrapped.setdefault("e", "z"))
        self.assertEqual("y", wrapped.setdefault("x", "y"))
        with self.assertRaises(KeyError):
            wrapped.pop("missing")
        self.assertEqual("f", wrapped.pop("e"))
        self.assertEqual(2, len(wrapped))
        self.assertEqual("q", wrapped.pop("missing", "q"))
        wrapped.clear()
        self.assertEqual(len(wrapped), 0)

        wrapped.metadata["k"] = "v"
        self.assertEqual({"k": "v"}, wrapped.metadata)

        self.assertIs(backing, wrapped.unwrap())
        double_wrap = _wrap.CollectionProxy(wrapped)
        self.assertIs(backing, double_wrap.unwrap())


class TestItem(unittest.TestCase):
    def test_get(self):
        the_a = _wrap.item(str)

        class ItemHaver(_wrap.CollectionProxy):

            a = the_a
            b = _wrap.item(int, "base_b")

        self.assertIs(the_a, ItemHaver.a)

        data = {}
        items = ItemHaver(data)
        items["c"] = "d"

        with self.assertRaises(AttributeError):
            items.a
        with self.assertRaises(AttributeError):
            items.b
        with self.assertRaises(AttributeError):
            del items.a

        self.assertEqual("d", items["c"])

        data["a"] = "a"
        data["base_b"] = 1
        self.assertEqual("a", items.a)
        self.assertEqual(1, items.b)

        items.a = "hello"
        items.b = 500

        self.assertEqual(dict(a="hello", base_b=500, c="d"), data)
        del items.a
        self.assertEqual(dict(base_b=500, c="d"), data)
