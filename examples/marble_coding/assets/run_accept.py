#!/usr/bin/env python3
"""Sealed acceptance runner for the ex-marble_coding TEACHING EXAMPLE.

The scored MARBLE cards run the real thing inside a pinned container:

    python -m pip install -q pytest==8.3.3 && \
      python -m pytest assets/gc-324/test_accept.py -q --tb=no -p no:cacheprovider

and extract the metric with the regex ``^(\\d+) passed``. This example has to
run with no docker, no pip install and no network, so this stdlib-only runner
stands in for ``pytest -q``: it executes the sealed unittest suite and prints
the SAME summary shapes pytest emits, so the grading contract -- including the
EXTRACT_FAIL trap on a partially passing suite -- is byte-compatible.

    all green   ->  ``14 passed``
    some red    ->  ``3 failed, 11 passed``
    all red     ->  ``14 failed``

(Real pytest appends ``in 0.03s``; the regex ignores the tail, and leaving it
out here keeps this example's captured output reproducible.) Failing tests are
listed by node id before the summary, because the process axis wants failure
identities, not counts.

Usage, from the workspace root:  python3 assets/run_accept.py
Exit code is 0 only when every test passes.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEST_FILE = HERE / "test_accept.py"

# keep __pycache__ out of the workspace: compiled artifacts embed absolute
# build paths and have no business in a sealed asset directory
sys.dont_write_bytecode = True


def load_suite() -> unittest.TestSuite:
    spec = importlib.util.spec_from_file_location("test_accept", TEST_FILE)
    module = importlib.util.module_from_spec(spec)
    sys.modules["test_accept"] = module
    spec.loader.exec_module(module)
    return unittest.defaultTestLoader.loadTestsFromModule(module)


def flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def node_id(test_id: str) -> str:
    """'test_accept.BookerTest.test_x' -> 'assets/test_accept.py::BookerTest::test_x'"""
    return "assets/test_accept.py::" + "::".join(test_id.split(".")[1:])


def main() -> int:
    suite = load_suite()
    tests = list(flatten(suite))
    result = unittest.TestResult()
    suite.run(result)

    bad = {t.id() for t, _ in result.failures} | {t.id() for t, _ in result.errors}
    passed = result.testsRun - len(bad)

    print("".join("F" if t.id() in bad else "." for t in tests))
    print()
    for test_id in sorted(bad):
        print("FAILED " + node_id(test_id))
    if bad and passed:
        print(f"{len(bad)} failed, {passed} passed")
    elif bad:
        print(f"{len(bad)} failed")
    else:
        print(f"{passed} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
