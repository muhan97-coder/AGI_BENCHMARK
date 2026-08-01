"""Sealed stage-2 acceptance suite for ex-campaign. Do not modify: the grader
hash-checks this file and runs its own pinned copy."""
import unittest

import kv


class TestRender(unittest.TestCase):
    def test_empty_mapping(self):
        self.assertEqual(kv.render({}), "")

    def test_sorted_by_key(self):
        self.assertEqual(kv.render({"b": "2", "a": "1"}), "a=1\nb=2\n")

    def test_round_trip(self):
        mapping = {"z": "last", "a": "first", "m": "middle"}
        self.assertEqual(kv.parse(kv.render(mapping)), mapping)


class TestMerge(unittest.TestCase):
    def test_b_wins(self):
        self.assertEqual(kv.merge({"a": "1", "b": "2"}, {"b": "9"}),
                         {"a": "1", "b": "9"})

    def test_inputs_not_mutated(self):
        a, b = {"a": "1"}, {"a": "2"}
        kv.merge(a, b)
        self.assertEqual((a, b), ({"a": "1"}, {"a": "2"}))

    def test_returns_new_object(self):
        a = {"a": "1"}
        self.assertIsNot(kv.merge(a, {}), a)


if __name__ == "__main__":
    unittest.main()
