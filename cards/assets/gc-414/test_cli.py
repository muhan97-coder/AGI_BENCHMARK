"""Sealed stage-3 CLI suite for gc-414 (read-only). Runs from repo root."""
import os
import subprocess
import sys

CLI = os.path.join("work", "gc-414", "cli.py")


def run(*args):
    return subprocess.run([sys.executable, CLI, *args], capture_output=True,
                          text=True, timeout=30)


def test_to_basic():
    r = run("to", "14")
    assert (r.returncode, r.stdout) == (0, "XIV\n")


def test_to_large():
    r = run("to", "3999")
    assert (r.returncode, r.stdout) == (0, "MMMCMXCIX\n")


def test_from_basic():
    r = run("from", "XIV")
    assert (r.returncode, r.stdout) == (0, "14\n")


def test_to_invalid_value():
    r = run("to", "4000")
    assert r.returncode == 2
    assert r.stdout == ""
    assert r.stderr.startswith("error:")


def test_to_non_integer():
    r = run("to", "abc")
    assert r.returncode == 2
    assert r.stdout == ""
    assert r.stderr.startswith("error:")


def test_from_invalid_numeral():
    r = run("from", "IIII")
    assert r.returncode == 2
    assert r.stdout == ""
    assert r.stderr.startswith("error:")


def test_unknown_subcommand():
    r = run("upto", "5")
    assert r.returncode == 2
    assert r.stdout == ""
    assert r.stderr.startswith("usage:")


def test_wrong_argc():
    r = run("to")
    assert r.returncode == 2
    assert r.stdout == ""
    assert r.stderr.startswith("usage:")
