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
    def test_values(self):
        for n, r in [(1,"I"),(4,"IV"),(9,"IX"),(14,"XIV"),(40,"XL"),(90,"XC"),
                     (400,"CD"),(944,"CMXLIV"),(1990,"MCMXC"),(3999,"MMMCMXCIX")]:
            self.assertEqual(S.to_roman(n), r)
    def test_range(self):
        for bad in (0, 4000, -3):
            with self.assertRaises(ValueError):
                S.to_roman(bad)

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(T)
    res = unittest.TestResult()
    suite.run(res)
    ok = res.testsRun > 0 and not res.failures and not res.errors
    print(json.dumps({"ok": ok, "ran": res.testsRun}))
