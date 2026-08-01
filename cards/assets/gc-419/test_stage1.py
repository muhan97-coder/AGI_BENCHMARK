"""Sealed stage-1 suite for gc-419 (read-only)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.getcwd(), "work", "gc-419"))

import logquery  # noqa: E402


def _write(tmp_path, text):
    p = tmp_path / "x.log"
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_load_basic(tmp_path):
    path = _write(tmp_path, "a=1 b=2\nlevel=info flag\n")
    assert logquery.load(path) == [{"a": "1", "b": "2"},
                                   {"level": "info", "flag": True}]


def test_load_skips_blank_lines(tmp_path):
    path = _write(tmp_path, "a=1\n\n   \nb=2\n")
    assert logquery.load(path) == [{"a": "1"}, {"b": "2"}]


def test_load_quoted_values(tmp_path):
    path = _write(tmp_path, 'msg="hello world" level=warn\n')
    assert logquery.load(path) == [{"msg": "hello world", "level": "warn"}]


def test_load_empty_file(tmp_path):
    assert logquery.load(_write(tmp_path, "")) == []


RECORDS = [{"level": "info", "bytes": "512", "svc": "api"},
           {"level": "error", "bytes": "7", "svc": "worker"},
           {"level": "info", "bytes": "90", "msg": "job done"},
           {"svc": "cron"}]


def test_filter_eq():
    got = logquery.filter_records(RECORDS, "level", "eq", "info")
    assert got == [RECORDS[0], RECORDS[2]]


def test_filter_ne_requires_key():
    got = logquery.filter_records(RECORDS, "level", "ne", "info")
    assert got == [RECORDS[1]]


def test_filter_contains():
    got = logquery.filter_records(RECORDS, "msg", "contains", "done")
    assert got == [RECORDS[2]]


def test_filter_gt():
    got = logquery.filter_records(RECORDS, "bytes", "gt", 80)
    assert got == [RECORDS[0], RECORDS[2]]


def test_filter_lt_excludes_non_numeric():
    recs = RECORDS + [{"bytes": "n/a"}]
    got = logquery.filter_records(recs, "bytes", "lt", "100")
    assert got == [RECORDS[1], RECORDS[2]]


def test_filter_unknown_op_raises():
    with pytest.raises(ValueError):
        logquery.filter_records(RECORDS, "level", "regex", "x")
