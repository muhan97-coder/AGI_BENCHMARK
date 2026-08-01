"""Sealed acceptance suite for gc-398 (semverx). Run from benchmark repo root."""
import importlib.util
import os

import pytest

_PATH = os.path.join(os.getcwd(), "workspace", "gc-398", "semverx.py")
_spec = importlib.util.spec_from_file_location("semverx_under_test", _PATH)
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


VALID = [
    "0.0.0", "1.2.3", "10.20.30", "1.0.0-alpha", "1.0.0-alpha.1",
    "1.0.0-0", "1.0.0-1", "1.0.0-alpha.0a1", "1.0.0-alpha-1",
    "1.0.0+001", "1.0.0+exp.sha.5114f85", "1.0.0-rc.1+build.1",
    "2.0.0-rc.1.2.3",
]

INVALID = [
    "01.0.0", "1.00.0", "1.0.00", "1.0", "1", "1.0.0.0", "1.0.0-",
    "1.0.0-alpha..1", "1.0.0-01", "1.0.0-alpha.01", "v1.0.0", " 1.0.0",
    "1.0.0 ", "1.0.0-alpha_beta", "1.0.0+", "1.0.0+a..b", "", "1.-1.0",
]


def test_valid_strings():
    for v in VALID:
        assert M.is_valid(v) is True, v


def test_invalid_strings():
    for v in INVALID:
        assert M.is_valid(v) is False, v


def test_parse_basic():
    d = M.parse("1.2.3")
    assert d == {"major": 1, "minor": 2, "patch": 3, "prerelease": [], "build": []}


def test_parse_prerelease_numeric_becomes_int():
    d = M.parse("1.0.0-alpha.1.0a1")
    assert d["prerelease"] == ["alpha", 1, "0a1"]


def test_parse_build_stays_str():
    d = M.parse("1.0.0+001.20.abc")
    assert d["build"] == ["001", "20", "abc"]


def test_parse_invalid_raises():
    with pytest.raises(ValueError):
        M.parse("1.0.0-01")


ORDER = ["1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta", "1.0.0-beta",
         "1.0.0-beta.2", "1.0.0-beta.11", "1.0.0-rc.1", "1.0.0"]


def test_semver_org_precedence_chain():
    for a, b in zip(ORDER, ORDER[1:]):
        assert M.compare(a, b) == -1, (a, b)
        assert M.compare(b, a) == 1, (b, a)


def test_compare_core_numeric():
    assert M.compare("1.9.0", "1.10.0") == -1
    assert M.compare("2.0.0", "1.99.99") == 1


def test_compare_equal():
    assert M.compare("1.2.3", "1.2.3") == 0


def test_prerelease_lower_than_release():
    assert M.compare("1.0.0-rc.999", "1.0.0") == -1


def test_numeric_prerelease_compares_numerically():
    assert M.compare("1.0.0-2", "1.0.0-11") == -1


def test_numeric_always_below_alphanumeric():
    assert M.compare("1.0.0-999999", "1.0.0-a") == -1


def test_longer_prerelease_wins_on_prefix_tie():
    assert M.compare("1.0.0-alpha", "1.0.0-alpha.0") == -1


def test_build_ignored_in_precedence():
    assert M.compare("1.0.0+a", "1.0.0+b") == 0
    assert M.compare("1.0.0-alpha+x.1", "1.0.0-alpha+y.2") == 0


def test_compare_invalid_raises():
    with pytest.raises(ValueError):
        M.compare("1.0.0", "01.0.0")


def test_max_version_simple():
    assert M.max_version(["1.0.0", "1.2.0", "1.1.9"]) == "1.2.0"


def test_max_version_prerelease_vs_release():
    assert M.max_version(["2.0.0-rc.1", "1.9.9"]) == "2.0.0-rc.1"
    assert M.max_version(["2.0.0-rc.1", "2.0.0"]) == "2.0.0"


def test_max_version_tie_returns_earliest():
    assert M.max_version(["1.0.0+bbb", "1.0.0+aaa"]) == "1.0.0+bbb"


def test_max_version_empty_raises():
    with pytest.raises(ValueError):
        M.max_version([])


def test_max_version_invalid_element_raises():
    with pytest.raises(ValueError):
        M.max_version(["1.0.0", "not-a-version"])
