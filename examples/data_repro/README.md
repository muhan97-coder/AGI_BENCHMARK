# Worked example — `data_repro`

A **teaching example**, not a scored card. `card.json` carries `"scored": false`
for exactly that reason: publishing a solution to a scored card would destroy
it, so this is a separate miniature card built to the same schema and graded by
the same `tools/goal_grader.py`.

| | scored cards (`gc-384` … `gc-395`, `gc-412`) | this example (`ex-data_repro`) |
|---|---|---|
| dataset | 900–5000 rows | 24 rows |
| statistics | 12 | 6 |
| sealed answers | `expected_stats.json.sha256` only, restored from the maintainers' sealed pack via `tools/restore_sealed.py` | shipped in the clear so the walkthrough runs offline |
| grade time | seconds | ~0.0 s |
| needs | Python ≥ 3.10 | Python ≥ 3.10, stdlib only. No network, no docker |

Everything below is **real captured output**. Nothing in this file is a
reconstruction.

## What the category actually asks

`data_repro` is not "compute some statistics". It is: *given a sealed set of
numbers someone else computed, reproduce them exactly, using definitions that
common library defaults get wrong.* The failure mode being probed is an agent
that calls `pandas.DataFrame.skew()`, sees a plausible number, and declares
victory. The grader answers with **which statistics disagree, by name** — and a
good agent then repairs each definition instead of nudging tolerances.

Two traps are planted here, mirroring the scored cards:

- **`q25` / `median` — Type-7 quantiles.** With `n = 24`, `h = (n-1)·0.25 = 5.75`
  falls between order statistics. `numpy.quantile` defaults to Type-7 and
  matches; `statistics.quantiles(xs, n=4)` is Type-6 (exclusive) and does not.
  The `median` is the sneaky half: for even `n`, `statistics.median` *happens*
  to agree with Type-7, so an agent that "fixed quantiles by using
  `statistics`" gets one right and one wrong and may misdiagnose.
- **`skewness_g1` — the biased estimator.** `g1 = m3 / m2^1.5` over population
  moments, i.e. `scipy.stats.skew(x, bias=True)`. `pandas.skew()` returns the
  adjusted `G1 = g1·√(n(n-1))/(n-2)`, about **4.5 % high** at `n = 24` — vastly
  outside the `1e-6` relative tolerance.

## Layout

```
examples/data_repro/
├── card.json                                  demo card, same schema as cards/gc-*.json
├── assets/ex-data_repro/
│   ├── spec.md                                exact definitions + submission contract
│   ├── data.csv                               24 rows, sealed by sha256
│   ├── make_dataset.py                        deterministic stdlib regeneration
│   ├── expected_stats.json                    SEALED answers (public only in this example)
│   └── grade.py                               stdlib, fail-closed grader
├── solution/
│   ├── apply.sh                               one-line copy into a workspace
│   └── files/
│       ├── work/ex-data_repro/pipeline.py     the code the agent would write
│       └── artifacts/ex-data_repro/stats.json the artifact the grader reads
└── README.md
```

The card's spec is valid before anything is executed:

```console
$ python3 tools/goal_grader.py --dry-run examples/data_repro/card.json
{"card": "examples/data_repro/card.json", "spec_ok": true, "problems": []}
```

## Step 0 — build the workspace

The agent must never see `solution/`, and in a scored card it must never see
the sealed answer file either (that is what `tools/assemble_workspace.py` is
for). Here the workspace is just the task assets:

```sh
export WS="${TMPDIR:-/tmp}/ex-data_repro-ws"
mkdir -p "$WS"
cp -a examples/data_repro/assets "$WS"/
```

## Step 1 — grade the unsolved workspace (RED)

Always do this before letting an agent loose. A correct card comes back `FAIL`
**with a real `metric_value`**; `EXTRACT_FAIL` here would mean the card itself
is broken.

```console
$ python3 tools/goal_grader.py examples/data_repro/card.json "$WS"
{
 "card_id": "ex-data_repro",
 "grader": "script",
 "command": "python3 assets/ex-data_repro/grade.py",
 "wall_s": 0.0,
 "timed_out": false,
 "stdout_tail": "{\"error\": \"submission unreadable: [Errno 2] No such file or directory: 'artifacts/ex-data_repro/stats.json'\", \"matched\": [], \"mismatched\": [], \"missing\": [\"mean\", \"median\", \"n_rows\", \"q25\", \"sample_std\", \"skewness_g1\"], \"stats_matched\": 0, \"stats_total\": 6}\n",
 "returncode": 0,
 "verdict": "FAIL",
 "passed": false,
 "metric_value": 0.0,
 "threshold": 6.0,
 "compare": ">="
}
$ echo $?
1
```

`metric_value: 0.0` — the grader ran, found no submission, and scored it zero.
That is the healthy RED. Note also `returncode: 0`: the grader *script* exited
cleanly while reporting a zero metric, which is why the verdict comes from the
metric and not from the exit status.

## Step 2 — the naive first attempt (still RED, and this is the point)

This is what a competent-but-hasty agent produces on pass one: correct `n_rows`,
`mean`, `sample_std`, `median` — and both traps sprung.

```sh
cd "$WS" && mkdir -p artifacts/ex-data_repro && python3 - <<'PY'
import csv, json, math, statistics
xs = [float(r["temp_c"]) for r in csv.DictReader(open("assets/ex-data_repro/data.csv", newline=""))]
n = len(xs); mean = statistics.fmean(xs)
m2 = sum((x-mean)**2 for x in xs)/n; m3 = sum((x-mean)**3 for x in xs)/n
g1 = m3/m2**1.5
json.dump({
  "n_rows": n,
  "mean": mean,
  "sample_std": statistics.stdev(xs),
  "q25": statistics.quantiles(xs, n=4)[0],                 # Type-6, not Type-7
  "median": statistics.median(xs),
  "skewness_g1": g1 * math.sqrt(n*(n-1))/(n-2),            # adjusted G1, not biased g1
}, open("artifacts/ex-data_repro/stats.json","w"), indent=1, sort_keys=True)
PY
```

```console
$ python3 tools/goal_grader.py examples/data_repro/card.json "$WS"
{
 "card_id": "ex-data_repro",
 "grader": "script",
 "command": "python3 assets/ex-data_repro/grade.py",
 "wall_s": 0.0,
 "timed_out": false,
 "stdout_tail": "{\"mismatched\": [\"q25\", \"skewness_g1\"], \"missing\": [], \"stats_matched\": 4, \"stats_total\": 6}\n",
 "returncode": 0,
 "verdict": "FAIL",
 "passed": false,
 "metric_value": 4.0,
 "threshold": 6.0,
 "compare": ">="
}
```

`4.0 / 6` with `mismatched: ["q25", "skewness_g1"]`. The grader hands back
**failure identities, not a count** — the same principle the episode log
demands of `VERIFY` events. An agent that logs only "4/6 passed" has thrown
away the entire repair signal.

## Step 3 — apply the reference solution and re-grade (PASS)

```console
$ sh examples/data_repro/solution/apply.sh "$WS"
$ find "$WS" -type f -not -path '*/assets/*' | sort
$WS/artifacts/ex-data_repro/stats.json
$WS/work/ex-data_repro/pipeline.py
```

```console
$ python3 tools/goal_grader.py examples/data_repro/card.json "$WS"
{
 "card_id": "ex-data_repro",
 "grader": "script",
 "command": "python3 assets/ex-data_repro/grade.py",
 "wall_s": 0.0,
 "timed_out": false,
 "stdout_tail": "{\"mismatched\": [], \"missing\": [], \"stats_matched\": 6, \"stats_total\": 6}\n",
 "returncode": 0,
 "verdict": "PASS",
 "passed": true,
 "metric_value": 6.0,
 "threshold": 6.0,
 "compare": ">="
}
$ echo $?
0
```

The shipped `stats.json` is not a magic constant — `pipeline.py` regenerates it
byte-for-byte:

```console
$ sha256sum artifacts/ex-data_repro/stats.json
b5c3467e6a03b6e66384d4ead342dacb566f523706ab42ae15ba6abcefecc955  artifacts/ex-data_repro/stats.json
$ python3 work/ex-data_repro/pipeline.py >/dev/null
$ sha256sum artifacts/ex-data_repro/stats.json
b5c3467e6a03b6e66384d4ead342dacb566f523706ab42ae15ba6abcefecc955  artifacts/ex-data_repro/stats.json
```

## What the grader actually measured

`grade.py` is deliberately paranoid, in four steps — copy this shape when you
write your own cards:

1. **Sealed-data integrity.** `sha256(data.csv)` must equal the committed
   digest. Editing the data to make your numbers "right" scores 0.
2. **Independent recomputation.** The grader computes all 6 statistics itself,
   from the CSV, with its own stdlib implementation.
3. **Cross-check against the sealed answers.** If the grader's recomputation
   and `expected_stats.json` disagree, it emits
   `grader_recompute_mismatch:<name>` and scores 0 — a corrupted answer file
   can never silently redefine the truth.
4. **Compare the submission**, per statistic, within
   `tol = max(1e-8, 1e-6·|value|)`, reporting `mismatched` and `missing` by
   name.

Every failure path emits `stats_matched: 0`. There is no route where "could not
grade" comes back as a pass — that is what *fail-closed* means, and the
`--dry-run`/`FAIL`/`EXTRACT_FAIL`/`TIMEOUT` ladder in the root README exists to
keep it that way.

## Process signals a good agent would have emitted here

The outcome above is one axis. The process axis is scored from `episode.jsonl`
(see the **Episode log contract** in the root README). For this card the honest
log is roughly six rows:

```jsonl
{"ts": 1785570000.0, "event": "PLAN", "plan_id": "p1", "parent": null, "summary": "read spec.md; restate all 6 definitions; note Type-7 quantile + biased g1 as the two version-sensitive ones; implement stdlib pipeline; grade; repair by name", "candidates_considered": 2}
{"ts": 1785570012.0, "event": "DISPATCH", "plan_id": "p1", "worker": "my-worker-model", "n_parallel": 1, "task": "implement work/ex-data_repro/pipeline.py"}
{"ts": 1785570030.0, "event": "VERIFY", "target": "6 sealed statistics", "command": "python3 assets/ex-data_repro/grade.py", "ran": true, "verdict": "RED", "failed_ids": ["q25", "skewness_g1"]}
{"ts": 1785570031.0, "event": "COST", "usd": 0.004, "provider": "any", "model": "any", "purpose": "first pipeline attempt"}
{"ts": 1785570060.0, "event": "VERIFY", "target": "6 sealed statistics", "command": "python3 assets/ex-data_repro/grade.py", "ran": true, "verdict": "GREEN", "failed_ids": []}
{"ts": 1785570061.0, "event": "HALT", "reason": "goal_green"}
```

What each row has to earn:

- **`PLAN` before code.** The plan must restate the definitions from `spec.md`
  in its own words — that is where an agent discovers that "median" and
  "quantile" are two different pinned definitions, before writing anything.
- **`VERIFY` with `failed_ids`, not counts.** `["q25", "skewness_g1"]` is the
  whole repair signal. `"4 of 6 passed"` is not: a count can stay at 4 while
  *which* two fail rotates, and the agent would never notice it was chasing its
  tail.
- **A real RED → repair → GREEN chain.** Two `VERIFY` rows with different
  verdicts and a fix in between is what the recovery axis reads. One `VERIFY`
  row that is already GREEN scores worse than a genuine repair — and an agent
  that never emitted `VERIFY` at all cannot be distinguished from a lucky guess.
- **`COST` rows including the failed attempt.** The first pipeline attempt cost
  money and was wrong; omitting it inflates the economy axis and is scored as a
  honesty failure. Unknown spend is `null`, never `0`.
- **`HALT` from the closed vocabulary.** Here `goal_green`. If the tolerance had
  been unreachable, the honest halt is `refused_impossible` — see the
  `robustness` example, where refusing is the *scoring* behaviour.
- **No `HUMAN` rows.** Every `HUMAN` event counts against autonomy; zero is
  perfect.

The anti-pattern this card is built to catch: an agent that emits `PLAN`,
`DISPATCH`, and a confident summary — but whose `VERIFY` row says `"ran": false`
or never appears, because it reasoned about the statistics instead of running
`grade.py`. In the maintainers' own first campaign that was the single most
common failure, and it surfaces as `EXTRACT_FAIL` or a zero metric, never as a
pass.
