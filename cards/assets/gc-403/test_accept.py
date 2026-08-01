"""Sealed acceptance suite for gc-403 (calcfrac). Run from benchmark repo root."""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

_DIR = os.path.join(os.getcwd(), "workspace", "gc-403")
_PATH = os.path.join(_DIR, "calcfrac.py")
_spec = importlib.util.spec_from_file_location("calcfrac_under_test", _PATH)
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


def cli(expr_args):
    return subprocess.run([sys.executable, _PATH, *expr_args],
                          capture_output=True, text=True, timeout=60)


def test_integer_addition():
    assert M.evaluate("1+2") == "3"


def test_precedence_mul_over_add():
    assert M.evaluate("2+3*4") == "14"


def test_parentheses():
    assert M.evaluate("(2+3)*4") == "20"


def test_fraction_output():
    assert M.evaluate("1/3") == "1/3"


def test_reduction():
    assert M.evaluate("2/4") == "1/2"
    assert M.evaluate("6/3") == "2"


def test_decimal_exact():
    assert M.evaluate("0.1+0.2") == "3/10"
    assert M.evaluate("0.125") == "1/8"


def test_left_assoc_division():
    assert M.evaluate("8/4/2") == "1"


def test_left_assoc_subtraction():
    assert M.evaluate("10-4-3") == "3"


def test_power_right_assoc():
    assert M.evaluate("2^3^2") == "512"


def test_negative_exponent():
    assert M.evaluate("2^-2") == "1/4"


def test_unary_minus_vs_power():
    assert M.evaluate("-2^2") == "-4"
    assert M.evaluate("(-2)^2") == "4"


def test_double_unary():
    assert M.evaluate("--3") == "3"
    assert M.evaluate("-+-3") == "3"


def test_fraction_base_power():
    assert M.evaluate("(2/3)^2") == "4/9"


def test_zero_power_rules():
    assert M.evaluate("0^0") == "1"
    assert M.evaluate("0^5") == "0"
    with pytest.raises(ZeroDivisionError):
        M.evaluate("0^-1")


def test_exact_roundtrip():
    assert M.evaluate("(1/3)*3") == "1"
    assert M.evaluate("1/3+1/6") == "1/2"


def test_negative_result_format():
    assert M.evaluate("(0-1)/3") == "-1/3"


def test_unary_in_denominator():
    # binary / followed by unary minus is legal per the grammar
    assert M.evaluate("1/-3") == "-1/3"


def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        M.evaluate("1/0")
    with pytest.raises(ZeroDivisionError):
        M.evaluate("1/(2-2)")


def test_non_integer_exponent_raises():
    with pytest.raises(ValueError):
        M.evaluate("2^(1/2)")
    with pytest.raises(ValueError):
        M.evaluate("2^0.5")


def test_syntax_errors():
    for bad in ["", "1+", "(1", "1)", "1 2", "1//2", "abc", ".5", "5.",
                "1..2", "+", "()", "1+*2"]:
        with pytest.raises(ValueError):
            M.evaluate(bad)


def test_whitespace_tolerated():
    assert M.evaluate("  1 +\t2 * 3 ") == "7"


def test_big_exact_arithmetic():
    assert M.evaluate("10^20/10^19") == "10"
    assert M.evaluate("(1/7)*(7/1)") == "1"


def test_cli_success():
    p = cli(["1/3 + 1/6"])
    assert p.returncode == 0
    assert json.loads(p.stdout.strip()) == {"result": "1/2"}


def test_cli_syntax_error():
    p = cli(["1+"])
    assert p.returncode == 2
    assert json.loads(p.stdout.strip()) == {"error": "syntax"}


def test_cli_division_error():
    p = cli(["1/0"])
    assert p.returncode == 3
    assert json.loads(p.stdout.strip()) == {"error": "division"}


def test_cli_domain_error():
    p = cli(["2^(1/2)"])
    assert p.returncode == 4
    assert json.loads(p.stdout.strip()) == {"error": "domain"}


def test_cli_usage_error():
    p = cli([])
    assert p.returncode == 5
    assert json.loads(p.stdout.strip()) == {"error": "usage"}
