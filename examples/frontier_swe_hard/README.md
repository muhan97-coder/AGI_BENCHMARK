# Worked example: `frontier_swe_hard`

> **This is a teaching example, not part of the benchmark.**
> `card.json` here carries `"scored": false` and the id `ex-frontier_swe_hard`.
> It mirrors the *shape* of the scored frontier cards at miniature scale and
> grades in about a second. It teaches the loop, not the difficulty.

## What the scored cards do, and what this demo does instead

| | scored `frontier_swe_hard` cards (gc-452 … gc-463) | this demo (`ex-frontier_swe_hard`) |
|---|---|---|
| instances | SWE-bench **Verified** instances, incl. the >4-hour human-effort band | 2 hand-written miniature repos |
| harness | `python3 -m swebench.harness.run_evaluation` (`swebench==4.1.0`) with pinned per-instance docker images | `assets/ex-frontier_swe_hard/mini_harness.py`, stdlib + pytest |
| threshold | e.g. 3 resolved out of 10 — deliberately far below the instance count | 1 of 2 |
| budget | up to $100, horizon up to a month | $0.50, ~20 minutes |
| metric | `resolved_instances` | identical |

The band exists because *breadth stops working*: at 3-of-10 you cannot win by
spraying one-line patches, you have to pick targets and go deep. This demo
reproduces that pressure in two ways rather than by being big:

1. **`demoorg__tinygraph-201` needs a coordinated multi-file change.** A new
   `CycleError` type in `graph.py`, its export from `__init__.py`, and the raise
   site in `traversal.py`. Patch one file and the sealed tests fail at import.
2. **`demoorg__tinyunits-202` has a trap.** The reported symptom (mile
   conversions off by ~0.02%) can be silenced by special-casing the two
   conversions named in the bug report. That makes `FAIL_TO_PASS` green and
   breaks a `PASS_TO_PASS` invariant — which is precisely what SWE-bench's
   `PASS_TO_PASS` set is for.

## Files

```
examples/frontier_swe_hard/
  card.json                                     the demo card
  assets/instances.txt                          sealed instance-id list (2 ids)
  assets/instances/<id>/problem_statement.md    the bug report
  assets/instances/<id>/repo/                   the "checkout"
  assets/instances/<id>/tests/                  sealed FAIL_TO_PASS / PASS_TO_PASS
  assets/mini_harness.py                        demo stand-in for the swebench harness
  solution/predictions.jsonl                    reference run: root-cause fix for 201, shallow fix for 202
  solution/predictions_all_resolved.jsonl       both instances fixed at the root cause
  solution/patches/demoorg__tinygraph-201.diff            3-file diff
  solution/patches/demoorg__tinyunits-202_shallow.diff    the trap (F2P green, P2P red)
  solution/patches/demoorg__tinyunits-202_rootcause.diff  the real fix (one constant)
  solution/apply.sh                             copies a predictions file into a workspace
```

**About the reference solution:** `predictions.jsonl` deliberately reaches
`resolved_instances = 1` — the card's bar — with one instance still red, because
that is what a real frontier run looks like and because the red instance shows
you a `PASS_TO_PASS` regression in the report instead of just telling you about
it. `predictions_all_resolved.jsonl` then shows the root-cause fix landing 2 of
2. Both are graded below, for real.

## Step 0 — validate the spec (no execution, $0)

```sh
python3 tools/goal_grader.py --dry-run examples/frontier_swe_hard/card.json
```

```json
{"card": "examples/frontier_swe_hard/card.json", "spec_ok": true, "problems": []}
```

## Step 1 — grade an empty workspace

```sh
WS="${TMPDIR:-/tmp}/ws-ex-frontier_swe_hard"
rm -rf "$WS" && mkdir -p "$WS/assets"
cp -r examples/frontier_swe_hard/assets "$WS/assets/ex-frontier_swe_hard"

python3 tools/goal_grader.py examples/frontier_swe_hard/card.json "$WS"
```

Real output:

```json
{
 "card_id": "ex-frontier_swe_hard",
 "grader": "swebench",
 "command": "python3 assets/ex-frontier_swe_hard/mini_harness.py --predictions runs/ex-frontier_swe_hard/predictions.jsonl --instances-dir assets/ex-frontier_swe_hard/instances --instance-ids-file assets/ex-frontier_swe_hard/instances.txt --work-dir work/ex-frontier_swe_hard/harness --report-dir . --run-id ex-frontier_swe_hard && python3 -c \"import json; r=json.load(open('ex-frontier_swe_hard.ex-frontier_swe_hard.json')); print(json.dumps({'resolved_instances': r['resolved_instances']}))\"",
 "wall_s": 0.0,
 "timed_out": false,
 "stdout_tail": "[harness] ERROR predictions file not found: runs/ex-frontier_swe_hard/predictions.jsonl\n",
 "returncode": 2,
 "verdict": "EXTRACT_FAIL",
 "passed": false,
 "error": "metric 'resolved_instances' not found in stdout"
}
```

`EXTRACT_FAIL` — the grader ran, the agent produced nothing to grade.

## Step 2 — grade the untouched baseline (empty patches)

```sh
mkdir -p "$WS/runs/ex-frontier_swe_hard"
for iid in $(cat examples/frontier_swe_hard/assets/instances.txt); do
  printf '{"instance_id": "%s", "model_name_or_path": "ex-frontier_swe_hard", "model_patch": ""}\n' "$iid"
done > "$WS/runs/ex-frontier_swe_hard/predictions.jsonl"

python3 tools/goal_grader.py examples/frontier_swe_hard/card.json "$WS"
```

Real output:

```json
{
 "card_id": "ex-frontier_swe_hard",
 "grader": "swebench",
 "command": "python3 assets/ex-frontier_swe_hard/mini_harness.py --predictions runs/ex-frontier_swe_hard/predictions.jsonl --instances-dir assets/ex-frontier_swe_hard/instances --instance-ids-file assets/ex-frontier_swe_hard/instances.txt --work-dir work/ex-frontier_swe_hard/harness --report-dir . --run-id ex-frontier_swe_hard && python3 -c \"import json; r=json.load(open('ex-frontier_swe_hard.ex-frontier_swe_hard.json')); print(json.dumps({'resolved_instances': r['resolved_instances']}))\"",
 "wall_s": 0.7,
 "timed_out": false,
 "stdout_tail": "[harness] demoorg__tinygraph-201 resolved=False f2p=0 passed, p2p=5 passed cause=f2p_unfixed: tests/test_fail_to_pass.py\n[harness] demoorg__tinyunits-202 resolved=False f2p=0 passed, p2p=5 passed cause=f2p_unfixed: tests/test_fail_to_pass.py::test_mile_to_foot_is_5280, tests/test_fail_to_pass.py::test_mile_to_kilometre_uses_the_international_mile\n[harness] report written: ex-frontier_swe_hard.ex-frontier_swe_hard.json\n[harness] resolved_instances=0/2\n{\"resolved_instances\": 0}\n",
 "returncode": 0,
 "verdict": "FAIL",
 "passed": false,
 "metric_value": 0.0,
 "threshold": 1.0,
 "compare": ">="
}
```

`FAIL` with a real metric — the healthy red. Read the two causes carefully,
they are different failure *kinds*:

* `tinyunits-202` names two failing test ids — the tests ran and asserted.
* `tinygraph-201` names only the file, `tests/test_fail_to_pass.py`. That is a
  **collection error**: the sealed tests do `from tinygraph import CycleError`
  and the symbol does not exist yet, so nothing could even be imported. An agent
  that reports "0 tests failed" here is lying to itself.

Both baselines show `p2p=5 passed`, so the pre-existing behaviour is green
before any patch. Every later `PASS_TO_PASS` failure is therefore caused by the
agent's own diff.

## Step 3 — apply the reference solution and re-grade

```sh
sh examples/frontier_swe_hard/solution/apply.sh "$WS"
python3 tools/goal_grader.py examples/frontier_swe_hard/card.json "$WS"
```

Real output:

```json
{
 "card_id": "ex-frontier_swe_hard",
 "grader": "swebench",
 "command": "python3 assets/ex-frontier_swe_hard/mini_harness.py --predictions runs/ex-frontier_swe_hard/predictions.jsonl --instances-dir assets/ex-frontier_swe_hard/instances --instance-ids-file assets/ex-frontier_swe_hard/instances.txt --work-dir work/ex-frontier_swe_hard/harness --report-dir . --run-id ex-frontier_swe_hard && python3 -c \"import json; r=json.load(open('ex-frontier_swe_hard.ex-frontier_swe_hard.json')); print(json.dumps({'resolved_instances': r['resolved_instances']}))\"",
 "wall_s": 0.7,
 "timed_out": false,
 "stdout_tail": "[harness] demoorg__tinygraph-201 resolved=True f2p=3 passed, p2p=5 passed\n[harness] demoorg__tinyunits-202 resolved=False f2p=2 passed, p2p=4 passed cause=p2p_regression: tests/test_pass_to_pass.py::test_mile_round_trip_is_lossless\n[harness] report written: ex-frontier_swe_hard.ex-frontier_swe_hard.json\n[harness] resolved_instances=1/2\n{\"resolved_instances\": 1}\n",
 "returncode": 0,
 "verdict": "PASS",
 "passed": true,
 "metric_value": 1.0,
 "threshold": 1.0,
 "compare": ">="
}
```

`PASS` at exactly the threshold — and look at instance 202. Its
`FAIL_TO_PASS` suite went **green** (`f2p=2 passed`) and it is still
**unresolved**, because the shallow patch broke a `PASS_TO_PASS` invariant. The
per-instance record from the report:

```json
{
 "resolved_instances": 1,
 "resolved_ids": [
  "demoorg__tinygraph-201"
 ],
 "unresolved_ids": [
  "demoorg__tinyunits-202"
 ],
 "demoorg__tinyunits-202": {
  "instance_id": "demoorg__tinyunits-202",
  "resolved": false,
  "empty_patch": false,
  "FAIL_TO_PASS": {
   "passed": 2,
   "ok": true,
   "failed_ids": [],
   "summary": "2 passed in 0.00s"
  },
  "PASS_TO_PASS": {
   "passed": 4,
   "ok": false,
   "failed_ids": [
    "tests/test_pass_to_pass.py::test_mile_round_trip_is_lossless"
   ],
   "summary": "1 failed, 4 passed in 0.02s"
  },
  "cause": "p2p_regression: tests/test_pass_to_pass.py::test_mile_round_trip_is_lossless"
 }
}
```

That is the lesson of the whole category in one record: *making the reported
symptom go away is not the same as fixing the fault.* The shallow patch
(`solution/patches/demoorg__tinyunits-202_shallow.diff`) special-cases `mi→km`
and `mi→ft` while leaving the wrong constant `1609.0` in the table, so a mile
converted to km and back is no longer itself.

## Step 4 — the root-cause fix, for contrast

```sh
sh examples/frontier_swe_hard/solution/apply.sh "$WS" predictions_all_resolved.jsonl
python3 tools/goal_grader.py examples/frontier_swe_hard/card.json "$WS"
```

Real output:

```json
{
 "card_id": "ex-frontier_swe_hard",
 "grader": "swebench",
 "command": "python3 assets/ex-frontier_swe_hard/mini_harness.py --predictions runs/ex-frontier_swe_hard/predictions.jsonl --instances-dir assets/ex-frontier_swe_hard/instances --instance-ids-file assets/ex-frontier_swe_hard/instances.txt --work-dir work/ex-frontier_swe_hard/harness --report-dir . --run-id ex-frontier_swe_hard && python3 -c \"import json; r=json.load(open('ex-frontier_swe_hard.ex-frontier_swe_hard.json')); print(json.dumps({'resolved_instances': r['resolved_instances']}))\"",
 "wall_s": 0.6,
 "timed_out": false,
 "stdout_tail": "[harness] demoorg__tinygraph-201 resolved=True f2p=3 passed, p2p=5 passed\n[harness] demoorg__tinyunits-202 resolved=True f2p=2 passed, p2p=5 passed\n[harness] report written: ex-frontier_swe_hard.ex-frontier_swe_hard.json\n[harness] resolved_instances=2/2\n{\"resolved_instances\": 2}\n",
 "returncode": 0,
 "verdict": "PASS",
 "passed": true,
 "metric_value": 2.0,
 "threshold": 1.0,
 "compare": ">="
}
```

The entire difference between step 3 and step 4 is one constant:
`"mi": 1609.0` → `"mi": 1609.344`, plus deleting the two special cases.

## What the grader actually measured

* One command, one number: the last JSON line's `resolved_instances`, compared
  `>= 1`. No LLM judgment anywhere.
* Per instance, `resolved` requires **patch applies** ∧ **all `FAIL_TO_PASS`
  pass** ∧ **all `PASS_TO_PASS` pass**. Steps 3 and 4 differ only in the third
  clause, and that is the whole grade for instance 202.
* Sealed tests are copied over the patched tree *after* the patch applies, so a
  diff that edits tests is silently overwritten before anything runs.
* Fail-closed: missing predictions → `EXTRACT_FAIL`; unparseable JSONL →
  `EXTRACT_FAIL`; a patch that does not apply → that instance is unresolved with
  `patch_apply_failed` as its cause. No path turns "ungradable" into a pass.

## Process signals a good agent emits here

Illustrative `episode.jsonl` — what a good loop *would* emit on this card (see
the [episode log contract](../../README.md#episode-log-contract-process-axis--v1-draft)):

```jsonl
{"ts": 1785660000.0, "event": "PLAN", "plan_id": "p1", "parent": null, "summary": "triage both instances before patching; 201 = multi-file (new exception type), 202 = suspicious constant; threshold is 1 of 2, so go deep on 201 first", "candidates_considered": 2}
{"ts": 1785660020.0, "event": "DISPATCH", "plan_id": "p1", "worker": "any-model", "n_parallel": 2, "task": "reproduce both faults from the problem statements"}
{"ts": 1785660090.0, "event": "VERIFY", "target": "baseline, no patches", "command": "python3 assets/ex-frontier_swe_hard/mini_harness.py --predictions runs/ex-frontier_swe_hard/predictions.jsonl ...", "ran": true, "verdict": "RED", "failed_ids": ["demoorg__tinygraph-201::tests/test_fail_to_pass.py (collection error)", "demoorg__tinyunits-202::tests/test_fail_to_pass.py::test_mile_to_kilometre_uses_the_international_mile"]}
{"ts": 1785660095.0, "event": "COST", "usd": 0.0032, "provider": "any", "model": "any", "purpose": "triage"}
{"ts": 1785660200.0, "event": "VERIFY", "target": "round 1: 201 three-file patch, 202 special-cased conversions", "command": "python3 assets/ex-frontier_swe_hard/mini_harness.py --predictions runs/ex-frontier_swe_hard/predictions.jsonl ...", "ran": true, "verdict": "RED", "failed_ids": ["demoorg__tinyunits-202::tests/test_pass_to_pass.py::test_mile_round_trip_is_lossless"]}
{"ts": 1785660205.0, "event": "COST", "usd": 0.0088, "provider": "any", "model": "any", "purpose": "round 1 patches"}
{"ts": 1785660240.0, "event": "PLAN", "plan_id": "p2", "parent": "p1", "summary": "202: the round-trip regression means the special case treated the symptom; the fault is the 1609.0 constant in _TO_METRES", "candidates_considered": 2}
{"ts": 1785660300.0, "event": "VERIFY", "target": "round 2: 202 constant corrected to 1609.344", "command": "python3 assets/ex-frontier_swe_hard/mini_harness.py --predictions runs/ex-frontier_swe_hard/predictions.jsonl ...", "ran": true, "verdict": "GREEN", "failed_ids": []}
{"ts": 1785660305.0, "event": "COST", "usd": 0.0021, "provider": "any", "model": "any", "purpose": "round 2 repair"}
{"ts": 1785660310.0, "event": "HALT", "reason": "goal_green"}
```

Reading that trace by axis:

* **planning** — triage is recorded *before* the first patch, and the re-plan
  `p2` names the causal hypothesis (`1609.0` is wrong) rather than "try harder".
* **verification** — every `VERIFY` carries `failed_ids`. Note that the round-1
  entry rotates the failure identity from a `FAIL_TO_PASS` id to a
  `PASS_TO_PASS` id: the *count* of failing instances stayed at 1 while the
  meaning changed completely. That is exactly why the contract requires
  identities, not counts.
* **recovery** — RED → re-plan → GREEN, with the second diff traceable to the
  named regression.
* **honesty** — a `COST` row for every round, including the round that produced
  the wrong fix. If budget had run out at step 3, the honest `HALT` reason is
  `budget_exhausted`, and `PASS` at threshold 1 with one documented unresolved
  instance is still a legitimate result.
* **autonomy** — no `HUMAN` events.

## Where this demo is deliberately unfaithful

* No docker, no HuggingFace dataset, no multi-GB images: the scored cards' real
  cost is the environment, and this demo removes it.
* Two toy repos of a few dozen lines. Verified instances in this band are rated
  1 to 4+ hours of *human* effort in projects like django, sympy, xarray and
  sphinx.
* The sealed tests and the solution are readable here. Scored cards list the
  sealed test filenames under `assets_visibility.sealed` so
  `tools/assemble_workspace.py` keeps them out of the agent's workspace, and
  their `contamination_risk` is `public_gold_exists` — hence the explicit
  no-gold-consultation clause in their `process_expectations`.
