import itertools
import unittest
from typing import Any, Iterable

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
        with self.assertRaises(TypeError):
            issubclass(slice, types.Slice)  # type: ignore[misc]
        with self.assertRaises(TypeError):
            isinstance(slice(None), types.Slice)  # type: ignore[misc]

    def test_is_slice_of(self):
        for sss_int in itertools.product((None, 1), (None, 1), (None, 1)):
            slc_int = slice(*sss_int)  # start, stop, step
            with self.subTest(slc_int):
                self.assertTrue(types.is_slice_of(slc_int, int))
                if slc_int != slice(None):
                    # Slices of one type are not slices of a disjoint type,
                    # except for the empty slice which is universal.
                    self.assertFalse(types.is_slice_of(slc_int, str))
        for sss_str in itertools.product((None, ""), (None, ""), (None, "")):
            slc_str = slice(*sss_str)  # start, stop, step
            with self.subTest(slc_str):
                self.assertTrue(types.is_slice_of(slc_str, str))
                if slc_str != slice(None):
                    self.assertFalse(types.is_slice_of(slc_str, int))

        # Non-slices
        self.assertFalse(types.is_slice_of(1, int))
        self.assertFalse(types.is_slice_of(range(10), int))

        # All slots must match
        slc_heterogeneous = slice("a", 1, ())
        self.assertFalse(types.is_slice_of(slc_heterogeneous, str))
        self.assertFalse(types.is_slice_of(slc_heterogeneous, int))
        self.assertFalse(types.is_slice_of(slc_heterogeneous, tuple))
        self.assertTrue(types.is_slice_of(slc_heterogeneous, object))
