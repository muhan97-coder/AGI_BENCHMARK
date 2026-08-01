"""Behavioural suite for tally.py.

The grader copies this file next to a (possibly mutated) tally.py and runs it
with unittest discovery, so the import is a bare module import -- no package,
no source introspection.
"""
import unittest

import tally


class TestNormalize(unittest.TestCase):
    def test_strips_then_lowercases(self):
        # kills m01: dropping .strip() leaves the surrounding spaces
        self.assertEqual(tally.normalize("  Ada  "), "ada")

    def test_already_normal_is_unchanged(self):
        self.assertEqual(tally.normalize("ada"), "ada")


class TestTally(unittest.TestCase):
    def test_counts_repeats_exactly(self):
        # kills m02: a first occurrence must count as 1, not 2
        self.assertEqual(tally.tally(["a", "a", "b"]), {"a": 2, "b": 1})

    def test_merges_case_and_whitespace(self):
        # also kills m01 through the tally surface
        self.assertEqual(tally.tally([" A ", "a", "A"]), {"a": 3})

    def test_empty_input_gives_empty_mapping(self):
        self.assertEqual(tally.tally([]), {})


class TestTopK(unittest.TestCase):
    def test_orders_by_descending_frequency(self):
        # kills m03: ascending frequency would put "rare" first
        items = ["common"] * 3 + ["mid"] * 2 + ["rare"]
        self.assertEqual(tally.top_k(items, 3), ["common", "mid", "rare"])

    def test_ties_broken_alphabetically(self):
        self.assertEqual(tally.top_k(["b", "a"], 2), ["a", "b"])

    def test_truncates_to_k(self):
        self.assertEqual(tally.top_k(["a", "a", "b", "c"], 1), ["a"])

    def test_zero_returns_empty_list(self):
        # kills m04: k == 0 is legal and must not raise
        self.assertEqual(tally.top_k(["a", "b"], 0), [])

    def test_negative_k_raises(self):
        with self.assertRaises(ValueError):
            tally.top_k(["a"], -1)


class TestShare(unittest.TestCase):
    def test_empty_input_is_zero(self):
        # exercises the m05 site; m05 is semantics-preserving, so no assertion
        # here or anywhere else can kill it
        self.assertEqual(tally.share([], "a"), 0.0)

    def test_share_uses_normalised_key(self):
        self.assertAlmostEqual(tally.share([" A ", "a", "b", "c"], "A"), 0.5)

    def test_absent_name_is_zero(self):
        self.assertEqual(tally.share(["a", "b"], "z"), 0.0)


if __name__ == "__main__":
    unittest.main()
