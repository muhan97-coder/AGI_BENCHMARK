# Worked example: `swe_bench`

> **This is a teaching example, not part of the benchmark.**
> `card.json` here carries `"scored": false` and the id `ex-swe_bench`. It is a
> miniature card built to mirror the *shape* of the scored `swe_bench` cards so
> you can watch a full RED → GREEN grading cycle in about a second. Nothing in
> this directory reveals anything about the scored cards, and passing it proves
> nothing except that your loop can close.

## What the scored cards do, and what this demo does instead

| | scored `swe_bench` cards (gc-300 … gc-323) | this demo (`ex-swe_bench`) |
|---|---|---|
| instances | real SWE-bench Lite instances, sealed id list | 3 hand-written miniature repos |
| harness | `python3 -m swebench.harness.run_evaluation` (`swebench==4.1.0`), **one pinned docker image per instance environment**, several GB each | `assets/ex-swe_bench/mini_harness.py`, stdlib + pytest, no docker, no network |
| agent output | `runs/<card>/predictions.jsonl` with `model_patch` diffs | identical |
| report | `<model>.<run_id>.json` in the repo root | identical |
| metric | `resolved_instances`, last-JSON-line extraction | identical |
| threshold | 1 … 8 resolved, per card | 2 of 3 |
| wall time | minutes to hours, tens of GB of disk | ~1 s |

`mini_harness.py` **is not SWE-bench**. It borrows SWE-bench's grading
contract — apply the predicted patch to a pristine checkout, then require every
`FAIL_TO_PASS` test to pass *and* every `PASS_TO_PASS` test to keep passing —
and applies it to toy repositories. Everything you learn here about the loop
(predictions format, report file, per-instance failure identities, why a green
`FAIL_TO_PASS` alone is not enough) transfers; nothing you learn here about the
*difficulty* transfers.

## Files

```
examples/swe_bench/
  card.json                                   the demo card (schema-identical to a scored card)
  assets/instances.txt                        sealed instance-id list
  assets/instances/<id>/problem_statement.md  the bug report the agent reads
  assets/instances/<id>/repo/                 the "checkout" to be patched
  assets/instances/<id>/tests/                sealed FAIL_TO_PASS / PASS_TO_PASS
  assets/mini_harness.py                      the demo stand-in for the swebench harness
  solution/predictions.jsonl                  the reference artifact an agent must produce
  solution/patches/<id>.diff                  the same three diffs, readable
  solution/apply.sh                           copies predictions.jsonl into a workspace
```

The three instances:

| instance id | fault | fix |
|---|---|---|
| `demoorg__tinycalc-101` | `percent_change()` raises `ZeroDivisionError` on a zero baseline | return `None` instead |
| `demoorg__tinypath-102` | `normalize()` lets `..` escape the root of an absolute path | clamp at root, keep relative `..` |
| `demoorg__tinydate-103` | `format_duration(0)` returns `""` | fall back to `"0s"` |

## Step 0 — validate the spec (no execution, $0)

```sh
python3 tools/goal_grader.py --dry-run examples/swe_bench/card.json
```

```json
{"card": "examples/swe_bench/card.json", "spec_ok": true, "problems": []}
```

## Step 1 — grade an empty workspace

Stage the agent-facing workspace (assets only — this is what
`tools/assemble_workspace.py` does for scored cards, laid out by hand here
because the demo assets live under `examples/`, not `cards/assets/`):

```sh
WS="${TMPDIR:-/tmp}/ws-ex-swe_bench"
rm -rf "$WS" && mkdir -p "$WS/assets"
cp -r examples/swe_bench/assets "$WS/assets/ex-swe_bench"

python3 tools/goal_grader.py examples/swe_bench/card.json "$WS"
```

Real output:

```json
{
 "card_id": "ex-swe_bench",
 "grader": "swebench",
 "command": "python3 assets/ex-swe_bench/mini_harness.py --predictions runs/ex-swe_bench/predictions.jsonl --instances-dir assets/ex-swe_bench/instances --instance-ids-file assets/ex-swe_bench/instances.txt --work-dir work/ex-swe_bench/harness --report-dir . --run-id ex-swe_bench && python3 -c \"import json; r=json.load(open('ex-swe_bench.ex-swe_bench.json')); print(json.dumps({'resolved_instances': r['resolved_instances']}))\"",
 "wall_s": 0.0,
 "timed_out": false,
 "stdout_tail": "[harness] ERROR predictions file not found: runs/ex-swe_bench/predictions.jsonl\n",
 "returncode": 2,
 "verdict": "EXTRACT_FAIL",
 "passed": false,
 "error": "metric 'resolved_instances' not found in stdout"
}
```

`EXTRACT_FAIL`, exit code 1. This is the verdict the root README warns about:
the grader ran, but there was no artifact to grade. On the scored cards this is
the single most common first result, and it almost always means the agent never
wrote `predictions.jsonl` — not that the card is broken.

## Step 2 — grade a workspace with empty patches

An agent that triaged the instances but shipped no diffs still produces a
well-formed predictions file:

```sh
mkdir -p "$WS/runs/ex-swe_bench"
for iid in $(cat examples/swe_bench/assets/instances.txt); do
  printf '{"instance_id": "%s", "model_name_or_path": "ex-swe_bench", "model_patch": ""}\n' "$iid"
done > "$WS/runs/ex-swe_bench/predictions.jsonl"

python3 tools/goal_grader.py examples/swe_bench/card.json "$WS"
```

Real output:

```json
{
 "card_id": "ex-swe_bench",
 "grader": "swebench",
 "command": "python3 assets/ex-swe_bench/mini_harness.py --predictions runs/ex-swe_bench/predictions.jsonl --instances-dir assets/ex-swe_bench/instances --instance-ids-file assets/ex-swe_bench/instances.txt --work-dir work/ex-swe_bench/harness --report-dir . --run-id ex-swe_bench && python3 -c \"import json; r=json.load(open('ex-swe_bench.ex-swe_bench.json')); print(json.dumps({'resolved_instances': r['resolved_instances']}))\"",
 "wall_s": 1.0,
 "timed_out": false,
 "stdout_tail": "[harness] demoorg__tinycalc-101 resolved=False f2p=0 passed, p2p=5 passed cause=f2p_unfixed: tests/test_fail_to_pass.py::test_zero_baseline_returns_none, tests/test_fail_to_pass.py::test_zero_baseline_with_zero_new_returns_none\n[harness] demoorg__tinypath-102 resolved=False f2p=0 passed, p2p=5 passed cause=f2p_unfixed: tests/test_fail_to_pass.py::test_extra_parents_clamp_at_root, tests/test_fail_to_pass.py::test_leading_parent_clamps_at_root, tests/test_fail_to_pass.py::test_only_parents_collapse_to_root\n[harness] demoorg__tinydate-103 resolved=False f2p=0 passed, p2p=6 passed cause=f2p_unfixed: tests/test_fail_to_pass.py::test_sub_second_renders_as_zero_seconds, tests/test_fail_to_pass.py::test_zero_renders_as_zero_seconds\n[harness] report written: ex-swe_bench.ex-swe_bench.json\n[harness] resolved_instances=0/3\n{\"resolved_instances\": 0}\n",
 "returncode": 0,
 "verdict": "FAIL",
 "passed": false,
 "metric_value": 0.0,
 "threshold": 2.0,
 "compare": ">="
}
```

Now it is `FAIL` **with a `metric_value`** — a healthy red. Note what the
harness handed you for free: every unresolved instance comes with the *test
identities* that are still failing, and the `p2p=` counts confirm the baseline
is otherwise green, so any later `PASS_TO_PASS` breakage is your patch's fault.
Those identities are exactly what a `VERIFY` event's `failed_ids` field is for.

## Step 3 — apply the reference solution and re-grade

```sh
sh examples/swe_bench/solution/apply.sh "$WS"
python3 tools/goal_grader.py examples/swe_bench/card.json "$WS"
```

Real output:

```json
{
 "card_id": "ex-swe_bench",
 "grader": "swebench",
 "command": "python3 assets/ex-swe_bench/mini_harness.py --predictions runs/ex-swe_bench/predictions.jsonl --instances-dir assets/ex-swe_bench/instances --instance-ids-file assets/ex-swe_bench/instances.txt --work-dir work/ex-swe_bench/harness --report-dir . --run-id ex-swe_bench && python3 -c \"import json; r=json.load(open('ex-swe_bench.ex-swe_bench.json')); print(json.dumps({'resolved_instances': r['resolved_instances']}))\"",
 "wall_s": 1.0,
 "timed_out": false,
 "stdout_tail": "[harness] demoorg__tinycalc-101 resolved=True f2p=2 passed, p2p=5 passed\n[harness] demoorg__tinypath-102 resolved=True f2p=3 passed, p2p=5 passed\n[harness] demoorg__tinydate-103 resolved=True f2p=2 passed, p2p=6 passed\n[harness] report written: ex-swe_bench.ex-swe_bench.json\n[harness] resolved_instances=3/3\n{\"resolved_instances\": 3}\n",
 "returncode": 0,
 "verdict": "PASS",
 "passed": true,
 "metric_value": 3.0,
 "threshold": 2.0,
 "compare": ">="
}
```

`PASS`, exit code 0. The report the harness left in the workspace root
(`ex-swe_bench.ex-swe_bench.json`), reduced to its headline fields:

```json
{
 "run_id": "ex-swe_bench",
 "model": "ex-swe_bench",
 "total_instances": 3,
 "resolved_instances": 3,
 "resolved_ids": [
  "demoorg__tinycalc-101",
  "demoorg__tinypath-102",
  "demoorg__tinydate-103"
 ],
 "unresolved_ids": []
}
```

## What the grader actually measured

* It ran **one shell command** and extracted **one number**. The last JSON line
  of stdout must contain `resolved_instances`; that value is compared with
  `>= 2`. Nothing else in the run is graded, and no model reads the output.
* `resolved` is not "the tests I was shown pass". For every instance the
  harness re-copies the sealed tests **over your patched tree, after your patch
  applies**, then requires both suites green. Patching a test file is
  overwritten; deleting one makes the run error, not pass.
* Fail-closed: a missing predictions file, malformed JSONL, or a patch that
  will not apply can only produce `EXTRACT_FAIL` / a lower count. There is no
  input for which "could not evaluate" becomes a pass.
* The threshold is 2 of 3, not 3 of 3 — like the scored cards, the bar is a
  count, so triage matters. Spending your whole budget on the instance you find
  most interesting is a losing strategy.

## Process signals a good agent emits here

Outcome is only one axis. The same run should leave an `episode.jsonl` (see the
[episode log contract](../../README.md#episode-log-contract-process-axis--v1-draft)).
Illustrative — this is what a good loop *would* emit on this card, not a
capture:

```jsonl
{"ts": 1785570000.0, "event": "PLAN", "plan_id": "p1", "parent": null, "summary": "triage 3 instances from problem statements; target all 3, threshold is 2", "candidates_considered": 3}
{"ts": 1785570004.0, "event": "DISPATCH", "plan_id": "p1", "worker": "any-model", "n_parallel": 3, "task": "diagnose+patch demoorg__tinycalc-101 / tinypath-102 / tinydate-103"}
{"ts": 1785570060.0, "event": "VERIFY", "target": "candidate patches, round 1", "command": "python3 assets/ex-swe_bench/mini_harness.py --predictions runs/ex-swe_bench/predictions.jsonl ...", "ran": true, "verdict": "RED", "failed_ids": ["demoorg__tinypath-102::tests/test_fail_to_pass.py::test_only_parents_collapse_to_root"]}
{"ts": 1785570062.0, "event": "COST", "usd": 0.0041, "provider": "any", "model": "any", "purpose": "round 1 patches"}
{"ts": 1785570075.0, "event": "PLAN", "plan_id": "p2", "parent": "p1", "summary": "tinypath: '/../..' must collapse to '/', not '/..' -- clamp when parts is empty and path is absolute", "candidates_considered": 2}
{"ts": 1785570120.0, "event": "VERIFY", "target": "candidate patches, round 2", "command": "python3 assets/ex-swe_bench/mini_harness.py --predictions runs/ex-swe_bench/predictions.jsonl ...", "ran": true, "verdict": "GREEN", "failed_ids": []}
{"ts": 1785570122.0, "event": "COST", "usd": 0.0017, "provider": "any", "model": "any", "purpose": "round 2 repair"}
{"ts": 1785570130.0, "event": "HALT", "reason": "goal_green"}
```

What each axis is reading in that trace:

* **planning** — a `PLAN` exists *before* the first patch, and the re-plan
  (`p2`, `parent: p1`) names a specific fault, not "try again".
* **verification** — `VERIFY` events have `ran: true` and carry **failure
  identities**, not counts. The card's own
  `process_expectations` ask for the same thing in `runs/ex-swe_bench/failures.md`.
* **recovery** — the RED → re-plan → GREEN chain is visible, and the second
  round is traceable to the named failing test.
* **honesty** — a `COST` row per billable call, including the round that failed.
* **autonomy** — no `HUMAN` events.
* **economy** — Σ `COST` against `budget_usd` (0.25 on this demo card).

The anti-pattern the process axis is built to catch: `PASS` with an empty
trace — no `VERIFY`, near-zero spend, implausibly short wall time. On a card
this small that is easy to fake by hand; on the scored cards it is not, which is
the entire point of `replay-verified` and `harness-run` trust tiers.

## Where this demo is deliberately unfaithful

* No docker, no pinned images, no HuggingFace dataset — so no environment boss
  fight. The scored cards' hardest part is the environment, and this demo
  removes it on purpose.
* The sealed tests ship in the open here (you can read them, and the solution).
  Scored cards list test filenames under `assets_visibility.sealed` so
  `tools/assemble_workspace.py` keeps them out of the agent's workspace.
* Three toy bugs, each a few lines. Real Lite instances are multi-file changes
  in large projects with real ambiguity in the problem statement.
* `contamination_risk` is `low` here; the scored `swe_bench` cards are
  `public_gold_exists` — the gold patches are in the public dataset, which is
  why their `process_expectations` include a no-gold-consultation clause.
