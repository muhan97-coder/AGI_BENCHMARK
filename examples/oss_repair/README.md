# Worked example: `oss_repair`

> **This is a teaching example, not part of the benchmark.**
> `card.json` here carries `"scored": false` and the id `ex-oss_repair`. It is a
> miniature card built to mirror the *shape* of the scored `oss_repair` cards so
> you can watch a full RED → GREEN grading cycle in about a second.

## What the scored cards do, and what this demo does instead

| | scored `oss_repair` cards (gc-336 … gc-347) | this demo (`ex-oss_repair`) |
|---|---|---|
| base state | `git clone` of a real project, `git rev-parse HEAD` must equal a pinned SHA | a snapshot in `assets/ex-oss_repair/upstream/`, `VERSION` must still read `0.3.1` |
| environment | pinned docker image (`python:3.11-bookworm`) + pinned pip installs | your local `python3` + `pytest`, no docker, no network |
| task | implement a feature the pinned release does not have, specified only by sealed tests | identical (a `stopwords=` option) |
| grader | re-copy sealed tests over the workspace, `pytest -q`, extract `^(\d+) passed` | identical |
| threshold | 5 sealed tests passing | identical |
| wall time | minutes (clone + image + installs) | ~0.2 s |

The grading *mechanism* is a faithful copy. Only the environment is removed.

## Why the pin check exists

The scored cards run

```sh
test "$(git -C work/gc-336/repo rev-parse HEAD)" = "<pinned sha>" && ...
```

so that repairs stay uncommitted working-tree edits at exactly the pinned
release — you cannot "fix" the bug by checking out a later version where
upstream already fixed it. This demo has no git clone, so it pins the base
state the same way with a file the agent must not touch:

```sh
test "$(cat work/ex-oss_repair/repo/VERSION)" = "0.3.1" && ...
```

Bump the version to pretend you shipped a new release and the grader stops
before pytest ever runs.

## Files

```
examples/oss_repair/
  card.json                                  the demo card (schema-identical to a scored card)
  assets/upstream/                           pinned base snapshot of slugmini 0.3.1 (read-only upstream)
  assets/tests/test_sealed_ex_oss_repair.py  the 5 sealed acceptance tests
  solution/repo/slugmini/__init__.py         the one file an agent has to change
  solution/apply.sh                          copies it into a workspace
```

The feature the sealed tests specify: `slugify(text, separator="-",
stopwords=None)` where `stopwords` entries are matched case-insensitively
against the extracted words and removed before joining — except that a filter
which would empty the slug entirely is ignored, and default behaviour stays
byte-identical.

## Step 0 — validate the spec (no execution, $0)

```sh
python3 tools/goal_grader.py --dry-run examples/oss_repair/card.json
```

```json
{"card": "examples/oss_repair/card.json", "spec_ok": true, "problems": []}
```

## Step 1 — grade an empty workspace

Stage the agent-facing workspace (assets only — the equivalent of what
`tools/assemble_workspace.py` does for scored cards):

```sh
WS="${TMPDIR:-/tmp}/ws-ex-oss_repair"
rm -rf "$WS" && mkdir -p "$WS/assets"
cp -r examples/oss_repair/assets "$WS/assets/ex-oss_repair"

python3 tools/goal_grader.py examples/oss_repair/card.json "$WS"
```

Real output:

```json
{
 "card_id": "ex-oss_repair",
 "grader": "pytest",
 "command": "test \"$(cat work/ex-oss_repair/repo/VERSION)\" = \"0.3.1\" && rm -rf work/ex-oss_repair/sealed_run && mkdir -p work/ex-oss_repair/sealed_run && cp assets/ex-oss_repair/tests/*.py work/ex-oss_repair/sealed_run/ && cd work/ex-oss_repair/sealed_run && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=../repo python3 -m pytest -q --noconftest -p no:cacheprovider .",
 "wall_s": 0.0,
 "timed_out": false,
 "stdout_tail": "",
 "returncode": 1,
 "verdict": "EXTRACT_FAIL",
 "passed": false,
 "error": "extract_regex did not match: '^(\\\\d+) passed'"
}
```

`EXTRACT_FAIL` with an empty `stdout_tail`: the `test "$(cat ...VERSION)"` guard
failed because the agent has not staged the repo yet, so the `&&` chain never
reached pytest. Fail-closed — an ungradable run is red, never a pass.

## Step 2 — stage the pinned snapshot, grade again (the real RED)

This is the first thing the card's goal asks for — the stand-in for "clone at
the pinned SHA":

```sh
mkdir -p "$WS/work/ex-oss_repair"
cp -r "$WS/assets/ex-oss_repair/upstream" "$WS/work/ex-oss_repair/repo"

python3 tools/goal_grader.py examples/oss_repair/card.json "$WS"
```

Real output (the `stdout_tail` field is the grader's last 2000 characters of
pytest output; its middle is elided here with a marker, everything else is
verbatim):

```json
{
 "card_id": "ex-oss_repair",
 "grader": "pytest",
 "command": "test \"$(cat work/ex-oss_repair/repo/VERSION)\" = \"0.3.1\" && rm -rf work/ex-oss_repair/sealed_run && mkdir -p work/ex-oss_repair/sealed_run && cp assets/ex-oss_repair/tests/*.py work/ex-oss_repair/sealed_run/ && cd work/ex-oss_repair/sealed_run && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=../repo python3 -m pytest -q --noconftest -p no:cacheprovider .",
 "wall_s": 0.2,
 "timed_out": false,
 "stdout_tail": "fy() got an unexpected keyword argument 'stopwords'\n\ntest_sealed_ex_oss_repair.py:9: TypeError\n___________________ test_stopwords_match_case_insensitively ____________________\n\n    def test_stopwords_match_case_insensitively():\n        from slugmini import slugify\n    \n>       assert slugify(\"A Tale [... ~1.4 KB of pytest tracebacks elided ...] =========================== short test summary info ============================\nFAILED test_sealed_ex_oss_repair.py::test_stopwords_are_dropped - TypeError: ...\nFAILED test_sealed_ex_oss_repair.py::test_stopwords_match_case_insensitively\nFAILED test_sealed_ex_oss_repair.py::test_dropping_a_middle_word_leaves_no_separator_run\nFAILED test_sealed_ex_oss_repair.py::test_stopwords_that_would_empty_the_slug_are_ignored\n4 failed, 1 passed in 0.02s\n",
 "returncode": 1,
 "verdict": "EXTRACT_FAIL",
 "passed": false,
 "error": "extract_regex did not match: '^(\\\\d+) passed'"
}
```

The same `stdout_tail` field, decoded, last 7 lines:

```
test_sealed_ex_oss_repair.py:32: TypeError
=========================== short test summary info ============================
FAILED test_sealed_ex_oss_repair.py::test_stopwords_are_dropped - TypeError: ...
FAILED test_sealed_ex_oss_repair.py::test_stopwords_match_case_insensitively
FAILED test_sealed_ex_oss_repair.py::test_dropping_a_middle_word_leaves_no_separator_run
FAILED test_sealed_ex_oss_repair.py::test_stopwords_that_would_empty_the_slug_are_ignored
4 failed, 1 passed in 0.02s
```

**This is the single most important thing to internalise about this card
family.** The run is red and the verdict is `EXTRACT_FAIL`, *not* `FAIL` — for
the mechanical reason the root README gives: a failing pytest run prints
`4 failed, 1 passed`, and the anchored regex `^(\d+) passed` does not match a
line that starts with `4 failed`. There is no partial credit here and no metric
to plot; on this family, red is red.

Also note what the output is worth even so: four **test identities**, not a
count. One test (`test_default_behaviour_is_unchanged`) already passes on the
pinned snapshot — that is the regression guard, and it must still pass at the
end.

## Step 3 — apply the reference solution and re-grade

```sh
sh examples/oss_repair/solution/apply.sh "$WS"
python3 tools/goal_grader.py examples/oss_repair/card.json "$WS"
```

Real output:

```json
{
 "card_id": "ex-oss_repair",
 "grader": "pytest",
 "command": "test \"$(cat work/ex-oss_repair/repo/VERSION)\" = \"0.3.1\" && rm -rf work/ex-oss_repair/sealed_run && mkdir -p work/ex-oss_repair/sealed_run && cp assets/ex-oss_repair/tests/*.py work/ex-oss_repair/sealed_run/ && cd work/ex-oss_repair/sealed_run && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=../repo python3 -m pytest -q --noconftest -p no:cacheprovider .",
 "wall_s": 0.2,
 "timed_out": false,
 "stdout_tail": ".....                                                                    [100%]\n5 passed in 0.01s\n",
 "returncode": 0,
 "verdict": "PASS",
 "passed": true,
 "metric_value": 5.0,
 "threshold": 5.0,
 "compare": ">="
}
```

`PASS`, exit code 0. The whole repair is one function in
`solution/repo/slugmini/__init__.py`:

```python
def slugify(text, separator="-", stopwords=None):
    tokens = words(text)
    if stopwords:
        dropped = {str(word).lower() for word in stopwords}
        kept = [token for token in tokens if token not in dropped]
        if kept:
            tokens = kept
    return separator.join(tokens)
```

Note that filtering happens on *extracted words*, after tokenisation — which is
why removing a word in the middle cannot leave a doubled separator behind, and
why the sealed test for that case passes without any string-level cleanup.

## What the grader actually measured

* One shell command, one number: `^(\d+) passed` from pytest's summary line,
  compared `>= 5`. No LLM judgment anywhere.
* **The base state is pinned.** The `VERSION` check runs first; fail it and
  nothing else executes (step 1 shows exactly that).
* **The sealed tests are re-copied over the workspace on every run**, into a
  fresh `sealed_run/` directory that is deleted first. Editing the copy of the
  tests in your workspace does nothing: your edits are overwritten before pytest
  starts.
* **Plugin autoloading and conftest collection are disabled**
  (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `--noconftest`, `-p no:cacheprovider`),
  so a stray `conftest.py` or an installed plugin cannot monkeypatch the suite
  into passing.
* Fail-closed everywhere: unstaged repo, wrong version, import error, or any
  failing test all land on `EXTRACT_FAIL`/red. There is no input for which
  "could not grade" becomes a pass.

## Process signals a good agent emits here

Illustrative `episode.jsonl` — what a good loop *would* emit on this card (see
the [episode log contract](../../README.md#episode-log-contract-process-axis--v1-draft)):

```jsonl
{"ts": 1785700000.0, "event": "PLAN", "plan_id": "p1", "parent": null, "summary": "stage pinned 0.3.1 snapshot, run grader for baseline RED, then add stopwords= to slugify in slugmini/__init__.py; 5 sealed tests, 1 is a regression guard", "candidates_considered": 3}
{"ts": 1785700030.0, "event": "VERIFY", "target": "baseline before any source edit", "command": "test \"$(cat work/ex-oss_repair/repo/VERSION)\" = \"0.3.1\" && ... python3 -m pytest -q --noconftest -p no:cacheprovider .", "ran": true, "verdict": "RED", "failed_ids": ["test_sealed_ex_oss_repair.py::test_stopwords_are_dropped", "test_sealed_ex_oss_repair.py::test_stopwords_match_case_insensitively", "test_sealed_ex_oss_repair.py::test_dropping_a_middle_word_leaves_no_separator_run", "test_sealed_ex_oss_repair.py::test_stopwords_that_would_empty_the_slug_are_ignored"]}
{"ts": 1785700035.0, "event": "DISPATCH", "plan_id": "p1", "worker": "any-model", "n_parallel": 1, "task": "add stopwords filtering to slugify()"}
{"ts": 1785700120.0, "event": "VERIFY", "target": "increment 1: naive string replacement before tokenising", "command": "... python3 -m pytest -q --noconftest -p no:cacheprovider .", "ran": true, "verdict": "RED", "failed_ids": ["test_sealed_ex_oss_repair.py::test_stopwords_that_would_empty_the_slug_are_ignored"]}
{"ts": 1785700125.0, "event": "COST", "usd": 0.0026, "provider": "any", "model": "any", "purpose": "increment 1"}
{"ts": 1785700150.0, "event": "PLAN", "plan_id": "p2", "parent": "p1", "summary": "filter after tokenisation and keep the unfiltered tokens when the filter empties the slug -- named by test_stopwords_that_would_empty_the_slug_are_ignored", "candidates_considered": 2}
{"ts": 1785700210.0, "event": "VERIFY", "target": "increment 2", "command": "... python3 -m pytest -q --noconftest -p no:cacheprovider .", "ran": true, "verdict": "GREEN", "failed_ids": []}
{"ts": 1785700215.0, "event": "COST", "usd": 0.0014, "provider": "any", "model": "any", "purpose": "increment 2"}
{"ts": 1785700220.0, "event": "HALT", "reason": "goal_green"}
```

Reading that trace by axis:

* **planning** — a `PLAN` before the first source edit, naming the target module
  and which sealed tests each step should turn green (the card's
  `process_expectations` ask for the same file at
  `work/ex-oss_repair/notes/plan.md`).
* **verification** — the *first* `VERIFY` runs before any edit. That baseline
  RED is what makes every later green meaningful; without it you cannot tell a
  repair from a test that was already passing.
* **recovery** — the RED after increment 1 shrinks from four failing identities
  to one, and `p2` names that identity as the reason for the next diff. Shrinking
  identity sets, not shrinking counts, is the evidence of real progress.
* **honesty** — a `COST` row per increment, including the one that failed. Zero
  is only allowed when the call was actually free; unknown is `null`, never `0`.
* **autonomy** — no `HUMAN` events.
* **economy** — Σ `COST` vs `budget_usd` (0.25 on this demo card).

A `PASS` with no `VERIFY` events, no baseline RED and near-zero wall time is
mechanically suspicious on this card family, and the process axis is designed to
say so out loud.

## Where this demo is deliberately unfaithful

* No git clone, no docker image, no pip install — so no environment boss fight,
  which on the scored cards is most of the real work.
* `slugmini` is invented for this example; the scored cards target real
  libraries (python-slugify, xmltodict, cachetools, arrow, networkx, …) at
  pinned release SHAs, where the surrounding code is large enough that finding
  the right seam is itself the task.
* `contamination_risk` is `low` here. The scored `oss_repair` cards are
  `public_gold_exists`: the fix may exist in upstream history past the pinned
  SHA, so their trajectories are expected to show independent diagnosis.
