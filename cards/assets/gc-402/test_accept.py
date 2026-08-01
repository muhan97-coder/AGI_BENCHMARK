"""Sealed acceptance suite for gc-402 (diffstat). Run from benchmark repo root."""
import importlib.util
import json
import os
import subprocess
import sys

_DIR = os.path.join(os.getcwd(), "workspace", "gc-402")
_PATH = os.path.join(_DIR, "diffstat.py")
_spec = importlib.util.spec_from_file_location("diffstat_under_test", _PATH)
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


SIMPLE = """diff --git a/src/app.py b/src/app.py
index 1111111..2222222 100644
--- a/src/app.py
+++ b/src/app.py
@@ -1,4 +1,5 @@
 import os
-x = 1
+x = 2
+y = 3
 print(x)
 # end
"""

TWO_FILES = SIMPLE + """diff --git a/README.md b/README.md
index 3333333..4444444 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Title
+New line.
"""

NEW_FILE = """diff --git a/newmod.py b/newmod.py
new file mode 100644
index 0000000..5555555
--- /dev/null
+++ b/newmod.py
@@ -0,0 +1,3 @@
+a = 1
+b = 2
+c = 3
"""

DELETED_FILE = """diff --git a/old.txt b/old.txt
deleted file mode 100644
index 6666666..0000000
--- a/old.txt
+++ /dev/null
@@ -1,2 +0,0 @@
-gone
-also gone
"""

BINARY = """diff --git a/img/logo.png b/img/logo.png
index 7777777..8888888 100644
Binary files a/img/logo.png and b/img/logo.png differ
"""

PURE_RENAME = """diff --git a/old/name.py b/new/name.py
similarity index 100%
rename from old/name.py
rename to new/name.py
"""

RENAME_WITH_EDIT = """diff --git a/lib/a.py b/lib/b.py
similarity index 90%
rename from lib/a.py
rename to lib/b.py
index 9999999..aaaaaaa 100644
--- a/lib/a.py
+++ b/lib/b.py
@@ -1,2 +1,2 @@
 keep
-old line
+new line
"""

NO_NEWLINE = """diff --git a/f.txt b/f.txt
index bbbbbbb..ccccccc 100644
--- a/f.txt
+++ b/f.txt
@@ -1 +1 @@
-alpha
\\ No newline at end of file
+beta
\\ No newline at end of file
"""

PLAIN = """--- lao\t2002-02-21 23:30:39.942229878 -0800
+++ tzu\t2002-02-21 23:30:50.442260588 -0800
@@ -1,3 +1,3 @@
-The Way that can be told
 of is not the eternal Way;
-The name that can be named
+The named is the mother
+of all things.
 is not the eternal name.
"""

TRAP = """diff --git a/notes.txt b/notes.txt
index ddddddd..eeeeeee 100644
--- a/notes.txt
+++ b/notes.txt
@@ -1,3 +1,3 @@
 header
--- looks like a file header
+++ but it is hunk content
 footer
"""

MULTI_HUNK = """diff --git a/m.py b/m.py
index fffffff..0000001 100644
--- a/m.py
+++ b/m.py
@@ -1,2 +1,2 @@
-a
+A
 b
@@ -10 +10,2 @@
 z
+extra
"""


def test_simple_counts():
    r = M.parse(SIMPLE)
    assert len(r["files"]) == 1
    f = r["files"][0]
    assert f["path"] == "src/app.py"
    assert f["added"] == 2 and f["removed"] == 1
    assert f["binary"] is False and f["renamed_from"] is None


def test_totals():
    r = M.parse(TWO_FILES)
    assert r["total_added"] == 3 and r["total_removed"] == 1


def test_two_files_order():
    r = M.parse(TWO_FILES)
    assert [f["path"] for f in r["files"]] == ["src/app.py", "README.md"]


def test_new_file_path_from_b_side():
    r = M.parse(NEW_FILE)
    f = r["files"][0]
    assert f["path"] == "newmod.py"
    assert f["added"] == 3 and f["removed"] == 0


def test_deleted_file_path_from_a_side():
    r = M.parse(DELETED_FILE)
    f = r["files"][0]
    assert f["path"] == "old.txt"
    assert f["added"] == 0 and f["removed"] == 2


def test_binary_file():
    r = M.parse(BINARY)
    f = r["files"][0]
    assert f["path"] == "img/logo.png"
    assert f["binary"] is True
    assert f["added"] == 0 and f["removed"] == 0


def test_pure_rename_no_hunks():
    r = M.parse(PURE_RENAME)
    f = r["files"][0]
    assert f["path"] == "new/name.py"
    assert f["renamed_from"] == "old/name.py"
    assert f["added"] == 0 and f["removed"] == 0


def test_rename_with_edit():
    r = M.parse(RENAME_WITH_EDIT)
    f = r["files"][0]
    assert f["path"] == "lib/b.py"
    assert f["renamed_from"] == "lib/a.py"
    assert f["added"] == 1 and f["removed"] == 1


def test_no_newline_marker_ignored():
    r = M.parse(NO_NEWLINE)
    f = r["files"][0]
    assert f["added"] == 1 and f["removed"] == 1


def test_plain_diff_tab_timestamp_paths():
    r = M.parse(PLAIN)
    f = r["files"][0]
    assert f["path"] == "tzu"
    assert f["added"] == 2 and f["removed"] == 2


def test_hunk_body_dashes_trap():
    r = M.parse(TRAP)
    assert len(r["files"]) == 1
    f = r["files"][0]
    assert f["path"] == "notes.txt"
    assert f["added"] == 1 and f["removed"] == 1


def test_multi_hunk_counts():
    r = M.parse(MULTI_HUNK)
    f = r["files"][0]
    assert f["added"] == 2 and f["removed"] == 1


def test_default_count_omitted_is_one():
    r = M.parse(MULTI_HUNK)  # second hunk header uses -10 (no count)
    assert r["files"][0]["path"] == "m.py"
    assert r["total_added"] == 2 and r["total_removed"] == 1


def test_context_lines_not_counted():
    r = M.parse(SIMPLE)
    assert r["total_added"] == 2 and r["total_removed"] == 1


def test_empty_input():
    assert M.parse("") == {"files": [], "total_added": 0, "total_removed": 0}


def test_concatenated_everything():
    text = SIMPLE + NEW_FILE + BINARY + RENAME_WITH_EDIT
    r = M.parse(text)
    assert [f["path"] for f in r["files"]] == [
        "src/app.py", "newmod.py", "img/logo.png", "lib/b.py"]
    assert r["total_added"] == 2 + 3 + 0 + 1
    assert r["total_removed"] == 1 + 0 + 0 + 1


def test_entry_field_shape():
    r = M.parse(SIMPLE)
    assert set(r["files"][0].keys()) == {
        "path", "added", "removed", "binary", "renamed_from"}


def test_plain_diff_multiple_blocks():
    text = PLAIN + PLAIN.replace("tzu", "second")
    r = M.parse(text)
    assert [f["path"] for f in r["files"]] == ["tzu", "second"]
    assert r["total_added"] == 4 and r["total_removed"] == 4


def test_cli_single_json_line():
    p = subprocess.run([sys.executable, _PATH], input=TWO_FILES,
                       capture_output=True, text=True, timeout=60)
    assert p.returncode == 0
    lines = [ln for ln in p.stdout.splitlines() if ln.strip()]
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj["total_added"] == 3 and obj["total_removed"] == 1
    assert len(obj["files"]) == 2


def test_cli_empty_stdin():
    p = subprocess.run([sys.executable, _PATH], input="",
                       capture_output=True, text=True, timeout=60)
    assert p.returncode == 0
    assert json.loads(p.stdout.strip()) == {
        "files": [], "total_added": 0, "total_removed": 0}
