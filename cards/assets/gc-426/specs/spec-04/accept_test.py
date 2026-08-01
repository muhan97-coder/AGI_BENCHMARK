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
    def test_true(self):
        for s in ("", "()", "a[b]{c}(d)", "([{}])"):
            self.assertTrue(S.balanced(s), s)
    def test_false(self):
        for s in ("(", ")(", "([)]", "{[}"):
            self.assertFalse(S.balanced(s), s)

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(T)
    res = unittest.TestResult()
    suite.run(res)
    ok = res.testsRun > 0 and not res.failures and not res.errors
    print(json.dumps({"ok": ok, "ran": res.testsRun}))
