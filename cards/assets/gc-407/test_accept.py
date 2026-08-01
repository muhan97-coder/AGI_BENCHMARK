"""Sealed acceptance suite for gc-407 (kvlog). Run from benchmark repo root."""
import json
import os
import subprocess
import sys

TOOL = os.path.join(os.getcwd(), "workspace", "gc-407", "kvlog.py")


def run(db, *args):
    return subprocess.run([sys.executable, TOOL, str(db), *args],
                          capture_output=True, text=True, timeout=60)


def out(db, *args):
    p = run(db, *args)
    assert p.returncode == 0, f"exit={p.returncode} stderr={p.stderr[:500]}"
    return json.loads(p.stdout.strip())


def raw(db):
    with open(db, "rb") as f:
        return f.read()


def test_set_get_roundtrip(tmp_path):
    db = tmp_path / "db.log"
    assert out(db, "set", "alpha", "one") == {"ok": True}
    assert out(db, "get", "alpha") == {"key": "alpha", "value": "one"}


def test_get_missing_key_notfound(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "a", "1")
    p = run(db, "get", "nope")
    assert p.returncode == 3
    assert json.loads(p.stdout.strip()) == {"error": "notfound"}


def test_get_on_missing_file_notfound(tmp_path):
    p = run(tmp_path / "absent.log", "get", "k")
    assert p.returncode == 3
    assert json.loads(p.stdout.strip()) == {"error": "notfound"}


def test_last_writer_wins(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "k", "v1")
    out(db, "set", "k", "v2")
    out(db, "set", "k", "v3")
    assert out(db, "get", "k") == {"key": "k", "value": "v3"}


def test_del_then_get_notfound(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "k", "v")
    assert out(db, "del", "k") == {"ok": True}
    p = run(db, "get", "k")
    assert p.returncode == 3


def test_del_missing_appends_nothing(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "a", "1")
    before = raw(db)
    p = run(db, "del", "ghost")
    assert p.returncode == 3
    assert json.loads(p.stdout.strip()) == {"error": "notfound"}
    assert raw(db) == before


def test_del_already_tombstoned_notfound(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "k", "v")
    out(db, "del", "k")
    before = raw(db)
    p = run(db, "del", "k")
    assert p.returncode == 3
    assert raw(db) == before


def test_set_after_del_revives(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "k", "old")
    out(db, "del", "k")
    out(db, "set", "k", "new")
    assert out(db, "get", "k") == {"key": "k", "value": "new"}


def test_keys_sorted_excludes_deleted(tmp_path):
    db = tmp_path / "db.log"
    for k, v in [("bb", "2"), ("aa", "1"), ("cc", "3")]:
        out(db, "set", k, v)
    out(db, "del", "bb")
    assert out(db, "keys") == {"keys": ["aa", "cc"]}


def test_keys_empty_store(tmp_path):
    assert out(tmp_path / "absent.log", "keys") == {"keys": []}


def test_file_format_exact_bytes(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "a", "1")
    out(db, "set", "b", "2")
    out(db, "del", "a")
    assert raw(db) == b"S\ta\t1\nS\tb\t2\nD\ta\n"


def test_empty_value_stored_and_returned(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "k", "")
    assert out(db, "get", "k") == {"key": "k", "value": ""}
    assert raw(db) == b"S\tk\t\n"


def test_value_with_spaces(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "k", "hello wide world")
    assert out(db, "get", "k") == {"key": "k", "value": "hello wide world"}


def test_unicode_value(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "k", "café ☃")
    assert out(db, "get", "k") == {"key": "k", "value": "café ☃"}


def test_usage_unknown_command(tmp_path):
    p = run(tmp_path / "db.log", "frob", "k")
    assert p.returncode == 2
    assert json.loads(p.stdout.strip()) == {"error": "usage"}


def test_usage_wrong_argc(tmp_path):
    db = tmp_path / "db.log"
    for args in [("get",), ("set", "k"), ("del",), ("keys", "x"),
                 ("set", "k", "v", "extra")]:
        p = run(db, *args)
        assert p.returncode == 2, args
        assert json.loads(p.stdout.strip()) == {"error": "usage"}


def test_usage_bad_key_writes_nothing(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "good", "v")
    before = raw(db)
    for bad in ["has space", "tab\tkey", "", "k$y", "sla/sh"]:
        p = run(db, "set", bad, "v")
        assert p.returncode == 2, bad
        assert json.loads(p.stdout.strip()) == {"error": "usage"}
    assert raw(db) == before


def test_usage_value_with_tab_or_newline(tmp_path):
    db = tmp_path / "db.log"
    for bad in ["a\tb", "a\nb", "a\rb"]:
        p = run(db, "set", "k", bad)
        assert p.returncode == 2
        assert json.loads(p.stdout.strip()) == {"error": "usage"}
    assert not os.path.exists(db)


def test_stats_counts(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "a", "1")
    out(db, "set", "b", "2")
    out(db, "set", "a", "3")
    out(db, "del", "b")
    assert out(db, "stats") == {"records": 4, "live": 1, "dead": 3}


def test_torn_tail_ignored_by_reads(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "a", "1")
    with open(db, "ab") as f:
        f.write(b"S\tzz\tpartial")  # no trailing newline: torn write
    assert out(db, "get", "a") == {"key": "a", "value": "1"}
    p = run(db, "get", "zz")
    assert p.returncode == 3
    assert out(db, "keys") == {"keys": ["a"]}
    assert out(db, "stats") == {"records": 1, "live": 1, "dead": 0}


def test_set_truncates_torn_tail_before_append(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "a", "1")
    with open(db, "ab") as f:
        f.write(b"S\tzz\tpar")
    out(db, "set", "b", "2")
    assert raw(db) == b"S\ta\t1\nS\tb\t2\n"
    assert out(db, "keys") == {"keys": ["a", "b"]}


def test_compact_repairs_torn_tail(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "b", "2")
    out(db, "set", "a", "1")
    with open(db, "ab") as f:
        f.write(b"D\tb")  # torn tombstone must NOT delete b
    assert out(db, "compact") == {"ok": True, "live": 2, "dropped": 0}
    assert raw(db) == b"S\ta\t1\nS\tb\t2\n"


def test_compact_drops_dead_and_sorts(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "b", "1")
    out(db, "set", "a", "2")
    out(db, "set", "b", "3")
    out(db, "set", "c", "4")
    out(db, "del", "c")
    assert out(db, "compact") == {"ok": True, "live": 2, "dropped": 3}
    assert raw(db) == b"S\ta\t2\nS\tb\t3\n"
    assert out(db, "stats") == {"records": 2, "live": 2, "dead": 0}


def test_compact_missing_file_creates_empty(tmp_path):
    db = tmp_path / "fresh.log"
    assert out(db, "compact") == {"ok": True, "live": 0, "dropped": 0}
    assert raw(db) == b""


def test_corrupt_interior_line_all_commands(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "a", "1")
    with open(db, "ab") as f:
        f.write(b"GARBAGE\n")
    out2 = run(db, "set", "b", "2")  # complete bad line -> corrupt
    for args in [("get", "a"), ("set", "b", "2"), ("del", "a"),
                 ("keys",), ("stats",), ("compact",)]:
        p = run(db, *args)
        assert p.returncode == 4, args
        assert json.loads(p.stdout.strip()) == {"error": "corrupt", "line": 2}
    assert out2.returncode == 4
    assert raw(db) == b"S\ta\t1\nGARBAGE\n"  # nothing was written


def test_corrupt_wrong_field_count(tmp_path):
    db = tmp_path / "db.log"
    with open(db, "wb") as f:
        f.write(b"S\tonlykey\nS\ta\t1\n")  # S with 2 fields at line 1
    p = run(db, "get", "a")
    assert p.returncode == 4
    assert json.loads(p.stdout.strip()) == {"error": "corrupt", "line": 1}


def test_corrupt_bad_opcode_and_key(tmp_path):
    db = tmp_path / "db.log"
    with open(db, "wb") as f:
        f.write(b"S\tok\tv\nX\tk\tv\n")
    p = run(db, "keys")
    assert p.returncode == 4
    assert json.loads(p.stdout.strip()) == {"error": "corrupt", "line": 2}
    with open(db, "wb") as f:
        f.write(b"S\tbad key\tv\n")  # invalid KEY in a complete record
    p = run(db, "keys")
    assert p.returncode == 4
    assert json.loads(p.stdout.strip()) == {"error": "corrupt", "line": 1}


def test_get_after_compact_full_cycle(tmp_path):
    db = tmp_path / "db.log"
    out(db, "set", "x", "1")
    out(db, "set", "y", "2")
    out(db, "del", "x")
    out(db, "compact")
    assert out(db, "get", "y") == {"key": "y", "value": "2"}
    p = run(db, "get", "x")
    assert p.returncode == 3
    out(db, "set", "x", "back")
    assert out(db, "get", "x") == {"key": "x", "value": "back"}


def test_many_records_scale(tmp_path):
    db = tmp_path / "db.log"
    for i in range(200):
        out(db, "set", f"k{i % 50:02d}", f"v{i}")
    assert out(db, "stats") == {"records": 200, "live": 50, "dead": 150}
    assert out(db, "get", "k49") == {"key": "k49", "value": "v199"}
    assert out(db, "compact") == {"ok": True, "live": 50, "dropped": 150}
    ks = out(db, "keys")["keys"]
    assert ks == sorted(ks) and len(ks) == 50
