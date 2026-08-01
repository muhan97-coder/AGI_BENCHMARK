# Worked example — `marble_coding`

A miniature of the scored MARBLE coding band (`gc-324`…`gc-335`), shrunk to one
class and 14 sealed tests so the whole EXTRACT_FAIL → RED → GREEN cycle runs in
under a second.

> **This card is not part of the benchmark.** `card.json` carries
> `"scored": false`. It exists so you can see the grading contract work
> end-to-end before you spend money on the real cards. Solutions to the scored
> cards are deliberately *not* published — publishing them would destroy them.

| | this example | the scored cards |
|---|---|---|
| task text | invented for this example | `multiagentbench/coding/coding_main.jsonl` in `MultiagentBench/MARBLE` at commit `8892e9c…` |
| deliverable | `workspace/solution.py` | `workspace/<card_id>/solution.py` |
| suite | 14 tests, sealed `assets/test_accept.py` | 14–17 tests, sealed `assets/<card_id>/test_accept.py` |
| runner | `python3 assets/run_accept.py` (stdlib) | `pip install -q pytest==8.3.3 && python -m pytest … -q --tb=no -p no:cacheprovider` inside `python:3.11.9-slim` |
| extraction | `^(\d+) passed`, threshold 14 | `^(\d+) passed`, threshold 14–17 |

**About the runner.** The scored cards run real pytest inside a pinned
container. This example must run with no docker, no pip and no network, so
`assets/run_accept.py` is a stdlib stand-in: it executes the same sealed
`unittest` suite and prints the same summary shapes pytest's `-q` mode emits
(`14 passed` / `1 failed, 13 passed` / `14 failed`), so the extraction contract
— including the `EXTRACT_FAIL` trap below — is byte-compatible with the real
thing. Real pytest appends `in 0.03s`; the regex ignores the tail, and omitting
it keeps the transcripts on this page reproducible.

## Layout

```
examples/marble_coding/
  card.json                    the demo card (same schema as cards/gc-*.json)
  assets/
    SPEC.md                    the interface contract — the agent's only brief
    test_accept.py             sealed acceptance suite (14 tests)
    run_accept.py              sealed runner (stdlib stand-in for `pytest -q`)
  solution/
    apply.sh                   copies the reference solution into a workspace
    workspace/solution.py      the single file an agent has to produce
  README.md                    this file
```

## 0. Validate the spec — free, executes nothing

```sh
python3 tools/goal_grader.py --dry-run examples/marble_coding/card.json
```

```json
{"card": "examples/marble_coding/card.json", "spec_ok": true, "problems": []}
```

## 1. Grade an empty workspace — real captured output

```sh
WS="${TMPDIR:-/tmp}/agi-bench-ex/marble_coding"
mkdir -p "$WS"
cp -R examples/marble_coding/assets "$WS/assets"

python3 tools/goal_grader.py examples/marble_coding/card.json "$WS"; echo "exit=$?"
```

```json
{
 "card_id": "ex-marble_coding",
 "grader": "pytest",
 "command": "python3 assets/run_accept.py",
 "wall_s": 0.0,
 "timed_out": false,
 "stdout_tail": "FFFFFFFFFFFFFF\n\nFAILED assets/test_accept.py::BookerTest::test_attendees_within_capacity\nFAILED assets/test_accept.py::BookerTest::test_booking_ids_increment_and_skip_rejections\nFAILED assets/test_accept.py::BookerTest::test_cancel_frees_the_slot\nFAILED assets/test_accept.py::BookerTest::test_cancel_requires_ownership\nFAILED assets/test_accept.py::BookerTest::test_cancel_unknown_booking_raises\nFAILED assets/test_accept.py::BookerTest::test_capacity_must_be_positive\nFAILED assets/test_accept.py::BookerTest::test_duplicate_room_rejected\nFAILED assets/test_accept.py::BookerTest::test_end_must_follow_start\nFAILED assets/test_accept.py::BookerTest::test_hours_stay_within_the_day\nFAILED assets/test_accept.py::BookerTest::test_notifications_in_delivery_order\nFAILED assets/test_accept.py::BookerTest::test_overlap_rejected_but_touching_allowed\nFAILED assets/test_accept.py::BookerTest::test_schedule_sorted_with_exact_keys\nFAILED assets/test_accept.py::BookerTest::test_unknown_room_raises_key_error\nFAILED assets/test_accept.py::BookerTest::test_utilization_and_busiest_room\n14 failed\n",
 "returncode": 1,
 "verdict": "EXTRACT_FAIL",
 "passed": false,
 "error": "extract_regex did not match: '^(\\\\d+) passed'"
}
exit=1
```

This is the `EXTRACT_FAIL` row from the root README's verdict table, and it is
the single most common first result people get. It does **not** mean the card
is broken. It means the command ran, produced output, and that output contained
no `N passed` line — because `workspace/solution.py` does not exist, so all 14
tests error in `setUp`. Fail-closed: no metric, no pass, exit 1.

The `stdout_tail` is the actionable part: 14 node ids, ready to be turned into
a plan.

### 1b. Thirteen of fourteen is still red

Suppose the agent implements everything except the overlap check. Real captured
output:

```json
{
 "card_id": "ex-marble_coding",
 "grader": "pytest",
 "command": "python3 assets/run_accept.py",
 "wall_s": 0.1,
 "timed_out": false,
 "stdout_tail": "..........F...\n\nFAILED assets/test_accept.py::BookerTest::test_overlap_rejected_but_touching_allowed\n1 failed, 13 passed\n",
 "returncode": 1,
 "verdict": "EXTRACT_FAIL",
 "passed": false,
 "error": "extract_regex did not match: '^(\\\\d+) passed'"
}
```

The summary line now reads `1 failed, 13 passed`. `^(\d+) passed` anchors at
the start of a line, matches `1`, then demands the literal ` passed` and finds
` failed` — so there is no metric at all, and the verdict is `EXTRACT_FAIL`
rather than `FAIL: 13 < 14`. **There is no partial credit on this axis.** The
root README says it in one line: *a failing pytest run prints `"N failed, M
passed"`, which regex `^(\d+) passed` does not match → EXTRACT_FAIL → red,
mechanically.* Here it is happening.

## 2. Apply the reference solution

```sh
sh examples/marble_coding/solution/apply.sh "$WS"
find "$WS" -type f | sort
```

```
$WS/assets/SPEC.md
$WS/assets/run_accept.py
$WS/assets/test_accept.py
$WS/workspace/solution.py
```

One file. That is the entire deliverable for a MARBLE coding card.

## 3. Grade again — real captured output

```sh
python3 tools/goal_grader.py examples/marble_coding/card.json "$WS"; echo "exit=$?"
```

```json
{
 "card_id": "ex-marble_coding",
 "grader": "pytest",
 "command": "python3 assets/run_accept.py",
 "wall_s": 0.0,
 "timed_out": false,
 "stdout_tail": "..............\n\n14 passed\n",
 "returncode": 0,
 "verdict": "PASS",
 "passed": true,
 "metric_value": 14.0,
 "threshold": 14.0,
 "compare": ">="
}
exit=0
```

## What the grader actually measured

Almost nothing about *how* the file was written, and everything about what it
does:

1. It ran the sealed suite from `assets/`, not from the workspace. Editing a
   copy of `test_accept.py` next to your solution changes nothing.
2. `SPEC.md` is the whole brief. Every rule the suite checks is stated there:
   ids start at 1, a rejected booking must not consume an id, `[start, end)`
   half-open intervals make touching endpoints legal, `schedule` rows carry
   exactly five keys, `busiest_room` breaks ties alphabetically. An agent that
   reads the spec closely writes the tie-break; an agent that guesses passes
   by luck on some inputs and fails on others.
3. The metric is `tests_passed`, extracted by `^(\d+) passed`, compared
   `>= 14`. Binary by construction.

A useful thing to notice about test 1b: the partial solution passed
`test_utilization_and_busiest_room` even with a `max()` tie-break that happened
to return the alphabetically-first room by insertion order. Passing is not the
same as being right — which is precisely why the benchmark also has a
[mutation band](../mutation_testing/README.md).

## Process signals a good agent would have emitted

The outcome above is one axis. The other six come from the agent's
`episode.jsonl` (see the [episode log contract](../../README.md#episode-log-contract-process-axis--v1-draft)):

```jsonl
{"ts": 1785570000.0, "event": "PLAN", "plan_id": "p1", "parent": null, "summary": "SPEC.md surfaces: rooms / booking validation / overlap / cancel / views; implement in that order", "candidates_considered": 5}
{"ts": 1785570005.0, "event": "DISPATCH", "plan_id": "p1", "worker": "any-model", "n_parallel": 1, "task": "increment 1: add_room + book validation"}
{"ts": 1785570045.0, "event": "VERIFY", "target": "increment 1", "command": "python3 assets/run_accept.py", "ran": true, "verdict": "RED", "failed_ids": ["assets/test_accept.py::BookerTest::test_cancel_frees_the_slot", "assets/test_accept.py::BookerTest::test_overlap_rejected_but_touching_allowed", "assets/test_accept.py::BookerTest::test_schedule_sorted_with_exact_keys", "assets/test_accept.py::BookerTest::test_utilization_and_busiest_room"], "workspace_ref": "<git sha>"}
{"ts": 1785570050.0, "event": "COST", "usd": 0.0038, "provider": "any", "model": "any", "purpose": "increment 1"}
{"ts": 1785570090.0, "event": "DISPATCH", "plan_id": "p1", "worker": "any-model", "n_parallel": 1, "task": "increment 2: overlap + cancel + views, targeting the 4 named reds"}
{"ts": 1785570140.0, "event": "VERIFY", "target": "increment 2", "command": "python3 assets/run_accept.py", "ran": true, "verdict": "RED", "failed_ids": ["assets/test_accept.py::BookerTest::test_overlap_rejected_but_touching_allowed"], "workspace_ref": "<git sha>"}
{"ts": 1785570145.0, "event": "COST", "usd": 0.0041, "provider": "any", "model": "any", "purpose": "increment 2"}
{"ts": 1785570180.0, "event": "PLAN", "plan_id": "p2", "parent": "p1", "summary": "re-read SPEC: intervals are half-open, so compare start < other.end and other.start < end", "candidates_considered": 3}
{"ts": 1785570210.0, "event": "VERIFY", "target": "final", "command": "python3 assets/run_accept.py", "ran": true, "verdict": "GREEN", "failed_ids": [], "workspace_ref": "<git sha>"}
{"ts": 1785570215.0, "event": "COST", "usd": 0.0022, "provider": "any", "model": "any", "purpose": "half-open interval fix"}
{"ts": 1785570220.0, "event": "HALT", "reason": "goal_green"}
```

What each event type has to carry on a card like this:

- **PLAN** — a decomposition into the SPEC surfaces *before* the first edit,
  and a second PLAN when the agent goes back to the spec instead of guessing at
  the overlap condition. `candidates_considered` is where breadth is scored: a
  planner that weighed three interval-comparison formulations and picked one
  reports 3, not 1.
- **DISPATCH** — which worker got which increment. `n_parallel: 1` is an honest
  answer for a single-file task; omitting the field is what costs points.
- **VERIFY** — **node ids, not counts.** `4 reds → 1 red → 0` is a recovery
  chain the scorer can see; "4 failing, then 1 failing" could equally be four
  different tests rotating. This is also why the runner prints
  `FAILED assets/test_accept.py::BookerTest::test_…` lines at all: the
  identities are the deliverable of a verification run, the count is a summary
  of it. `workspace_ref` (a git SHA) is what lifts a submission from
  `self-reported` to `replay-verified` — a sampled VERIFY event gets replayed
  at that state and the named failures must reproduce.
- **COST** — one row per billable call including the two that produced red
  code. `budget_usd` here is 0.5; the economy axis is Σ COST against it.
- **HALT** — `goal_green`. Note the failure mode this card makes easy: after the
  `1 failed, 13 passed` run an agent can *believe* it is 93% done and halt with
  a self-reported near-success. The grader says `EXTRACT_FAIL`, and an
  `episode.jsonl` whose last VERIFY is RED but whose HALT says `goal_green` is
  mechanically inconsistent — the honesty axis reads exactly that kind of
  mismatch.

No `HUMAN` events appear: zero is a perfect autonomy score.
