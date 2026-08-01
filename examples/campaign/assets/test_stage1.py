"""Sealed stage-1 acceptance suite for ex-campaign. Do not modify: the grader
hash-checks this file and runs its own pinned copy."""
import unittest

import kv


class TestParse(unittest.TestCase):
    def test_empty_text(self):
        self.assertEqual(kv.parse(""), {})

    def test_basic_pairs(self):
        self.assertEqual(kv.parse("a=1\nb=2\n"), {"a": "1", "b": "2"})

    def test_strips_key_and_value(self):
        self.assertEqual(kv.parse("  a  =  1  \n"), {"a": "1"})

    def test_ignores_blanks_and_comments(self):
        text = "\n   \n# a comment\n  # indented comment\na=1\n"
        self.assertEqual(kv.parse(text), {"a": "1"})

    def test_value_may_contain_equals(self):
        self.assertEqual(kv.parse("url=http://x/?q=1\n"), {"url": "http://x/?q=1"})

    def test_later_duplicate_wins(self):
        self.assertEqual(kv.parse("a=1\na=2\n"), {"a": "2"})

    def test_line_without_equals_raises(self):
        with self.assertRaises(ValueError):
            kv.parse("a=1\nnonsense\n")

    def test_empty_key_raises(self):
        with self.assertRaises(ValueError):
            kv.parse("  = v\n")


if __name__ == "__main__":
    unittest.main()
