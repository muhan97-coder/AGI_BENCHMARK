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
    def test_valid(self):
        self.assertTrue(S.luhn_valid("79927398713"))
        self.assertTrue(S.luhn_valid("4539578763621486"))
    def test_invalid(self):
        self.assertFalse(S.luhn_valid("79927398714"))
        self.assertFalse(S.luhn_valid("1234567812345678"))

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(T)
    res = unittest.TestResult()
    suite.run(res)
    ok = res.testsRun > 0 and not res.failures and not res.errors
    print(json.dumps({"ok": ok, "ran": res.testsRun}))
