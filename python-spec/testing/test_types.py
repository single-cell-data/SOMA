from typing import Any, Iterable
import unittest

from somacore import types


class TestTypes(unittest.TestCase):
    def test_is_nonstringy_sequence(self):
        seqs: Iterable[Any] = ([], (), range(10))
        for seq in seqs:
            with self.subTest(seq):
                self.assertTrue(types.is_nonstringy_sequence(seq))

        non_seqs: Iterable[Any] = (1, "hello", b"goodbye", (x for x in range(10)))
        for non_seq in non_seqs:
            with self.subTest(non_seq):
                self.assertFalse(types.is_nonstringy_sequence(non_seq))

    def test_slice(self):
        self.assertIsInstance(slice(None), types.Slice)
        self.assertNotIsInstance((1, 2), types.Slice)
