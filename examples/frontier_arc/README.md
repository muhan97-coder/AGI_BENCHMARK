# Worked example — `frontier_arc`

A **teaching example**, not a benchmark card. `card.json` here carries
`"scored": false` and its own reference solution ships in `solution/`. It exists
so you can exercise the ARC prediction contract — file layout, attempt shapes,
cell-exact scoring — offline, before spending a frontier budget on tasks that
state-of-the-art systems mostly fail.

| | scored cards (gc-440 … gc-451) | this example |
|---|---|---|
| tasks | sealed ids from ARC-AGI-2 at a pinned commit | **3 hand-made puzzles**, no dataset file copied |
| gold | downloaded from the pinned public repo at grade time | ships in `assets/ex-frontier_arc/gold/` (offline) |
| difficulty | frontier — gc-447 asks for 2 of 15 public-eval tasks | trivial by design; the *contract* is the lesson |
| grader | `python3 assets/gc-440/grade.py` → `{"solved": N}` | `python3 assets/ex-frontier_arc/grade.py` → same line, same rules |
| wall time | minutes plus network | milliseconds, stdlib only |

The three puzzles: `ex01_fall` (per-column gravity), `ex02_mirror` (row
concatenated with its mirror — **two test inputs**), `ex03_recolor` (a cyclic
colour map). Each task file has the same shape as an ARC task: `train` pairs with
`input`/`output`, and `test` entries carrying **only** `input`.

---

## 0. Set up a workspace

```sh
WS="${TMPDIR:-/tmp}/ws-ex-frontier_arc"
mkdir -p "$WS" && cp -a examples/frontier_arc/assets "$WS"/
```

If you point an agent at this workspace, strip the grader's gold first — on the
scored cards it is not reachable at all, because it lives in a remote repo the
grader fetches at grade time:

```sh
rm -rf "$WS/assets/ex-frontier_arc/gold"   # agent-facing workspace only, not the grading one
```

```console
$ python3 tools/goal_grader.py --dry-run examples/frontier_arc/card.json
{"card": "examples/frontier_arc/card.json", "spec_ok": true, "problems": []}
```

## 1. Grade the unsolved workspace — RED, with a real metric

```console
$ python3 tools/goal_grader.py examples/frontier_arc/card.json "$WS"
{
 "card_id": "ex-frontier_arc",
 "grader": "script",
 "command": "python3 assets/ex-frontier_arc/grade.py",
 "wall_s": 0.0,
 "timed_out": false,
 "stdout_tail": "{\"solved\": 0}\n",
 "returncode": 0,
 "verdict": "FAIL",
 "passed": false,
 "metric_value": 0.0,
 "threshold": 2.0,
 "compare": ">="
}
```

`FAIL` with `metric_value: 0.0`, **not** `EXTRACT_FAIL` — and that distinction is
designed in. A missing predictions file is a normal, expected state, so the
grader still prints a well-formed verdict; it just certifies nothing:

```console
$ python3 assets/ex-frontier_arc/grade.py
[grade ex-frontier_arc] predictions file missing: runs/ex-frontier_arc/predictions.json
{"solved": 0}
```

Everything the grader could not confirm becomes 0, never a pass. Unreadable JSON,
a wrong root type, gold it cannot load — all of it lands on `{"solved": 0}`.

## 2. Apply the reference solution

```sh
sh examples/frontier_arc/solution/apply.sh "$WS"
```

```console
$ find "$WS"/runs -type f | sort
.../runs/ex-frontier_arc/ledger.json
.../runs/ex-frontier_arc/plan.md
.../runs/ex-frontier_arc/predictions.json
```

Only `predictions.json` is graded. `plan.md` (hypotheses, each checked against
every train pair, plus the rejected variants) and `ledger.json` (per-task
attempts, spend, outcome) are the artifacts the card's `process_expectations`
demand — the process axis has nothing to read without them.

`predictions.json` deliberately uses all three accepted entry shapes:

```jsonc
{
  "ex01_fall":    [[0,0,0,0], ...],                             // bare grid — single-test shorthand
  "ex02_mirror":  [ {"attempt_1": [[0,9,0,0,9,0], ...],         // test input 1 of 2
                     "attempt_2": [...]},
                    [[3,0,0,4,4,0,0,3], ...] ],                 // test input 2, bare grid
  "ex03_recolor": [ {"attempt_1": [...], "attempt_2": [...]} ]  // two distinct rules
}
```

The `attempt_2` grids are *different rules*, not re-rolls: for `ex03_recolor` the
inverse colour permutation, for `ex02_mirror` the mirror placed on the other side.
Two attempts at the same rule are one attempt with extra steps.

## 3. Grade again — GREEN

```console
$ python3 tools/goal_grader.py examples/frontier_arc/card.json "$WS"
{
 "card_id": "ex-frontier_arc",
 "grader": "script",
 "command": "python3 assets/ex-frontier_arc/grade.py",
 "wall_s": 0.0,
 "timed_out": false,
 "stdout_tail": "{\"solved\": 3}\n",
 "returncode": 0,
 "verdict": "PASS",
 "passed": true,
 "metric_value": 3.0,
 "threshold": 2.0,
 "compare": ">="
}
```

`3 >= 2` — the threshold is a floor, and the metric is reported as measured, so a
run that clears it by a margin still says so. The grader's stderr is the per-task
identity feed a repair loop reads:

```console
$ python3 assets/ex-frontier_arc/grade.py
[grade ex-frontier_arc] ex01_fall SOLVED
[grade ex-frontier_arc] ex02_mirror SOLVED
[grade ex-frontier_arc] ex03_recolor SOLVED
{"solved": 3}
```

## 3b. Why "all test outputs or nothing" bites

`ex02_mirror` has two test inputs. Ship one entry instead of two — the first
grid perfectly correct — and the whole task scores zero. In a second workspace
(`WS2`), with `predictions["ex02_mirror"]` truncated to its first entry:

```console
$ python3 assets/ex-frontier_arc/grade.py
[grade ex-frontier_arc] ex01_fall SOLVED
[grade ex-frontier_arc] ex02_mirror not-solved
[grade ex-frontier_arc] ex03_recolor SOLVED
{"solved": 2}

$ python3 tools/goal_grader.py examples/frontier_arc/card.json "$WS2"
{
 "card_id": "ex-frontier_arc",
 "grader": "script",
 "command": "python3 assets/ex-frontier_arc/grade.py",
 "wall_s": 0.0,
 "timed_out": false,
 "stdout_tail": "{\"solved\": 2}\n",
 "returncode": 0,
 "verdict": "PASS",
 "passed": true,
 "metric_value": 2.0,
 "threshold": 2.0,
 "compare": ">="
}
```

Still a pass here, because the threshold is 2 of 3 — but on gc-447 (2 of 15) that
same slip is the difference between the card and nothing. Count your test inputs.

---

## What the grader actually measured

`tools/goal_grader.py` ran `python3 assets/ex-frontier_arc/grade.py`, took the
**last JSON line** of stdout, read `solved`, and compared it to `threshold: 2`
with `>=`. The grader itself:

1. reads the sealed id list `task_ids.txt`;
2. loads gold for each id (in the scored cards: downloads it from the pinned
   commit — unfetchable gold means `{"solved": 0}`, never a pass);
3. normalizes each per-test entry to **at most two attempt grids**, rejecting
   anything that is not a rectangular grid of ints 0–9;
4. counts a test output as matched if **any** attempt equals gold cell-exactly,
   and a task as solved only if **every** one of its test outputs matched.

No partial credit inside a task, no tolerance, no LLM judging a "close enough"
grid. The reason the miniature is worth walking through is that most first-run
failures on the real cards are contract failures, not reasoning failures: entries
in the wrong order, one entry for a two-test task, grids nested one level too
deep, `"1"` strings instead of ints.

## What good process would have looked like here

Episode-log shape for this card (see the root README for the contract) —
**illustrative, not a captured run**:

```jsonl
{"event":"PLAN","plan_id":"p1","summary":"triage 3 tasks cheapest-hypothesis-first; 2 attempts/test on distinct rules; verify with grade.py","candidates_considered":3}
{"event":"VERIFY","target":"ex03_recolor hypothesis","command":"check rule on all 3 train pairs","ran":true,"verdict":"GREEN","failed_ids":[]}
{"event":"VERIFY","target":"ex02_mirror hypothesis","command":"check rule on all 3 train pairs","ran":true,"verdict":"RED","failed_ids":["train[0]: mirror placed on the wrong side"]}
{"event":"VERIFY","target":"checkpoint","command":"python3 assets/ex-frontier_arc/grade.py","ran":true,"verdict":"RED","failed_ids":["ex02_mirror"]}
{"event":"COST","usd":0.01,"purpose":"hypothesis search"}
{"event":"VERIFY","target":"final","command":"python3 assets/ex-frontier_arc/grade.py","ran":true,"verdict":"GREEN","failed_ids":[]}
{"event":"HALT","reason":"goal_green"}
```

- **planning** — `runs/ex-frontier_arc/plan.md` exists before the first
  prediction, and names per-task priority, attempt budget and the exact
  verification command. `candidates_considered` reflects real triage breadth.
- **verification** — the load-bearing event here is the *train-pair* VERIFY, not
  the grader run. A hypothesis is checked against every train pair before a
  single test grid is emitted; the grader is the last check, not the first.
- **recovery** — a rejected hypothesis is logged by task id together with the
  revision that replaced it (see `hypotheses_rejected` in `ledger.json`), so
  RED → revise → GREEN is reconstructible.
- **honesty** — `ledger.json` records abandoned tasks and failed grader runs too.
  On `public_gold_exists` cards this is what separates a solve from a lookup: the
  log must show the rule *derived from train pairs*, and gold is off-limits as an
  input even though it is technically reachable.
- **autonomy / economy** — no `HUMAN` events; Σ`COST` against `budget_usd`.

`DISPATCH` is where the frontier cards diverge from this demo: three toy puzzles
need no fan-out, while gc-447's fifteen frontier tasks over a month-long campaign
are exactly the case for parallel workers on independent tasks — with one
`DISPATCH` row per attempt so the economy axis can see what the search cost.

## Running the real thing

```sh
python3 tools/goal_grader.py --dry-run cards/gc-440_arc2_training5_smoke.json
```

The scored cards need `raw.githubusercontent.com` reachable at grade time (gold
is fetched from a pinned commit and cached under `runs/<card>/gold_cache/`), and
they carry `contamination_risk: public_gold_exists` — the gold for the public
splits is on the internet, which is precisely why the process trace, not the
score alone, is what makes a frontier result believable.
