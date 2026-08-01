"""Sealed stage-3 integration suite for gc-415 (read-only). Repo root cwd."""
import os
import subprocess
import sys

REPORT = os.path.join("work", "gc-415", "report.py")
SAMPLE = os.path.join("assets", "gc-415", "sample_input.txt")
GOLDEN = os.path.join("assets", "gc-415", "expected_report.txt")


def run(*args):
    return subprocess.run([sys.executable, REPORT, *args],
                          capture_output=True, text=True, timeout=30)


def test_golden_report():
    r = run(SAMPLE)
    want = open(GOLDEN, "r", encoding="utf-8").read()
    assert r.returncode == 0
    assert r.stdout == want


def test_small_inline_case(tmp_path):
    p = tmp_path / "tiny.txt"
    p.write_text("x x y", encoding="utf-8")
    r = run(str(p))
    assert r.returncode == 0
    assert r.stdout == ("| word | count |\n"
                        "| ---- | ----- |\n"
                        "| x    | 2     |\n"
                        "| y    | 1     |\n")


def test_string_contents_not_counted(tmp_path):
    p = tmp_path / "s.txt"
    p.write_text('"only strings here"', encoding="utf-8")
    r = run(str(p))
    assert r.returncode == 0
    assert r.stdout == "| word | count |\n| ---- | ----- |\n"


def test_usage_wrong_argc():
    r = run()
    assert r.returncode == 2
    assert r.stdout == ""
    assert r.stderr.startswith("usage:")


def test_missing_file_error():
    r = run(os.path.join("work", "gc-415", "no_such_file.txt"))
    assert r.returncode == 1
    assert r.stdout == ""
    assert r.stderr.startswith("error:")


def test_tokenize_error_reported(tmp_path):
    p = tmp_path / "bad.txt"
    p.write_text("hello @ world", encoding="utf-8")
    r = run(str(p))
    assert r.returncode == 1
    assert r.stdout == ""
    assert r.stderr.startswith("error:")
