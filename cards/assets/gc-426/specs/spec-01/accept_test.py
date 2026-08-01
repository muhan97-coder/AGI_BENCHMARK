#!/usr/bin/env python3
"""Sealed acceptance test. Usage: python3 accept_test.py <solution.py>
Prints {"ok": bool, "ran": N} as the last line."""
import importlib.util, json, sys, unittest

def load(path):
    spec = importlib.util.spec_from_file_location("solution", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

try:
    S = load(sys.argv[1])
except Exception:
    print(json.dumps({"ok": False, "ran": 0}))
    sys.exit(0)


class T(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(S.rle_encode("aaabbc"), "a3b2c1")
    def test_single(self):
        self.assertEqual(S.rle_encode("z"), "z1")
    def test_empty(self):
        self.assertEqual(S.rle_encode(""), "")
    def test_alternating(self):
        self.assertEqual(S.rle_encode("ababab"), "a1b1a1b1a1b1")

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(T)
    res = unittest.TestResult()
    suite.run(res)
    ok = res.testsRun > 0 and not res.failures and not res.errors
    print(json.dumps({"ok": ok, "ran": res.testsRun}))
