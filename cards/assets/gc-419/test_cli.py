"""Sealed stage-4 CLI suite for gc-419 (read-only). Repo root cwd."""
import os
import subprocess
import sys

CLI = os.path.join("work", "gc-419", "cli.py")
SAMPLE = os.path.join("assets", "gc-419", "sample.log")


def run(*args):
    return subprocess.run([sys.executable, CLI, *args], capture_output=True,
                          text=True, timeout=30)


def test_golden_count_by_level():
    want = open(os.path.join("assets", "gc-419", "expected_countby.txt"),
                "r", encoding="utf-8").read()
    r = run("count-by", "level", SAMPLE)
    assert r.returncode == 0
    assert r.stdout == want


def test_golden_stats_bytes():
    want = open(os.path.join("assets", "gc-419", "expected_stats.txt"),
                "r", encoding="utf-8").read()
    r = run("stats", "bytes", SAMPLE)
    assert r.returncode == 0
    assert r.stdout == want


def test_inline_count_by(tmp_path):
    p = tmp_path / "t.log"
    p.write_text("k=a\nk=b\nk=a\n", encoding="utf-8")
    r = run("count-by", "k", str(p))
    assert r.returncode == 0
    assert r.stdout == "a 2\nb 1\n"


def test_usage_wrong_argc():
    r = run("count-by", "level")
    assert r.returncode == 2
    assert r.stdout == ""
    assert r.stderr.startswith("usage:")


def test_usage_unknown_subcommand():
    r = run("histogram", "level", SAMPLE)
    assert r.returncode == 2
    assert r.stdout == ""
    assert r.stderr.startswith("usage:")


def test_missing_file_error():
    r = run("count-by", "level", os.path.join("work", "gc-419", "nope.log"))
    assert r.returncode == 1
    assert r.stdout == ""
    assert r.stderr.startswith("error:")


def test_stats_without_numeric_values_error(tmp_path):
    p = tmp_path / "t.log"
    p.write_text("k=a\nk=b\n", encoding="utf-8")
    r = run("stats", "k", str(p))
    assert r.returncode == 1
    assert r.stdout == ""
    assert r.stderr.startswith("error:")
