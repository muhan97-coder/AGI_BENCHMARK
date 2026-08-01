# Worked example — `tool_from_spec`

A **teaching example**, not a scored card. `card.json` carries `"scored": false`:
publishing a solution to a scored card would destroy it, so this is a separate
miniature card built to the same schema and graded by the same
`tools/goal_grader.py`.

| | scored cards (`gc-396` … `gc-407`) | this example (`ex-tool_from_spec`) |
|---|---|---|
| tool | e.g. `wordtally`, `csvcast`, `microjson` | `numstat` |
| acceptance tests | 21–40 | 12 |
| grade time | seconds | ~0.4 s |
| needs | Python ≥ 3.10 + pinned `pytest` | same. No network, no docker |

Everything below is **real captured output**.

> The transcripts were produced with `python3` pointing at a throwaway venv
> (`$TMPDIR/exbench-venv`) so that the pytest tracebacks — which echo
> `sys.executable` — contain no machine-specific paths. Any Python ≥ 3.10 with
> pytest works.

## What the category actually asks

`tool_from_spec` gives the agent a written spec and a **sealed acceptance
suite** it must not read as a shortcut and must never edit. The grading shape is
the one described in the root README:

```
metric: "passed", extract_regex: "^(\\d+) passed", threshold: 12, compare: ">="
```

That regex is doing real work, and it is worth understanding before you run
anything. `pytest -q` ends a fully green run with `12 passed in 0.26s` — the
line begins with the number, so group 1 extracts `12`. A run with *any* failure
ends with `7 failed, 5 passed in 0.26s`. That line starts with `7 failed`, so
`^(\d+) passed` does not match at all, and the verdict is **`EXTRACT_FAIL`, not
`FAIL`**. Partial credit does not exist in this category by construction: you
either produce the whole contract or the metric is unextractable.

The spec plants the usual divergences, chosen so that one confident pass misses
them:

- **`skipped` vs. filtered.** `skipped` counts tokens that failed
  *classification*; values rejected by `--min` are not skipped, they are merely
  not kept. Most first drafts fold both into one counter.
- **Totals are pre-truncation.** `kept` and `sum` are computed before `--top`
  truncates `entries`. `--top 1` must not change them.
- **Tie-break direction.** Equal counts sort by value **ascending**.
- **`--min` defaults to *no bound*, not `0`.** Negative values are ordinary
  values.
- **Usage errors are a contract, not a convenience.** Exactly
  `{"error": "usage"}` on **stdout**, exit code **2**. `argparse` will not do
  this for you: it writes its own message to stderr, and it silently accepts
  `--top -1` and abbreviations. Deferring to it fails the last test.

## Layout

```
examples/tool_from_spec/
├── card.json                                       demo card, same schema as cards/gc-*.json
├── assets/ex-tool_from_spec/
│   ├── SPEC.md                                     the written contract
│   └── test_accept.py                              sealed acceptance suite (12 tests)
├── solution/
│   ├── apply.sh                                    one-line copy into a workspace
│   └── files/workspace/ex-tool_from_spec/numstat.py  the file the agent must produce
└── README.md
```

The card's spec is valid before anything is executed:

```console
$ python3 tools/goal_grader.py --dry-run examples/tool_from_spec/card.json
{"card": "examples/tool_from_spec/card.json", "spec_ok": true, "problems": []}
```

## Step 0 — build the workspace

```sh
export WS="${TMPDIR:-/tmp}/ex-tool_from_spec-ws"
mkdir -p "$WS"
cp -a examples/tool_from_spec/assets "$WS"/
```

The agent gets `SPEC.md` and `test_accept.py` and nothing else. It must never
see `solution/`.

## Step 1 — grade the unsolved workspace (RED)

```console
$ python3 tools/goal_grader.py examples/tool_from_spec/card.json "$WS"
{
 "card_id": "ex-tool_from_spec",
 "grader": "pytest",
 "command": "python3 -m pytest assets/ex-tool_from_spec/test_accept.py -q --tb=line -p no:cacheprovider",
 "wall_s": 0.3,
 "timed_out": false,
 "stdout_tail": "xbench-venv/bin/python3: can't open file '/tmp/ex-tool_from_spec-ws/workspace/ex-tool_from_spec/numstat.py': [Errno 2] No such file or directory\n      \n    assert 2 == 0\n     +  where 2 = CompletedProcess(args=['/tmp/exbench-venv/bin/python3', '/tmp/ex-tool_from_spec-ws/workspace/ex-tool_from_spec/numstat...t open file '/tmp/ex-tool_from_spec-ws/workspace/ex-tool_from_spec/numstat.py': [Errno 2] No such file or directory\\n\").returncode\n/tmp/ex-tool_from_spec-ws/assets/ex-tool_from_spec/test_accept.py:28: AssertionError: exit=2 stderr=/tmp/exbench-venv/bin/python3: can't open file '/tmp/ex-tool_from_spec-ws/workspace/ex-tool_from_spec/numstat.py': [Errno 2] No such file or directory\nE   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)\n/usr/lib/python3.12/json/decoder.py:355: json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)\n=========================== short test summary info ============================\nFAILED assets/ex-tool_from_spec/test_accept.py::test_basic_counts_and_sum - A...\nFAILED assets/ex-tool_from_spec/test_accept.py::test_empty_input_is_not_an_error\nFAILED assets/ex-tool_from_spec/test_accept.py::test_whitespace_runs_and_newlines_split\nFAILED assets/ex-tool_from_spec/test_accept.py::test_negative_values_are_values\nFAILED assets/ex-tool_from_spec/test_accept.py::test_non_integer_tokens_are_skipped\nFAILED assets/ex-tool_from_spec/test_accept.py::test_min_filter_excludes_but_does_not_count_as_skipped\nFAILED assets/ex-tool_from_spec/test_accept.py::test_min_accepts_negative_bound\nFAILED assets/ex-tool_from_spec/test_accept.py::test_tie_break_by_value_ascending\nFAILED assets/ex-tool_from_spec/test_accept.py::test_default_top_is_three - A...\nFAILED assets/ex-tool_from_spec/test_accept.py::test_top_truncates_after_totals_are_computed\nFAILED assets/ex-tool_from_spec/test_accept.py::test_top_zero_emits_empty_entries\nFAILED assets/ex-tool_from_spec/test_accept.py::test_usage_errors_exit_two_with_json\n12 failed in 0.13s\n",
 "returncode": 1,
 "verdict": "EXTRACT_FAIL",
 "passed": false,
 "error": "extract_regex did not match: '^(\\\\d+) passed'"
}
$ echo $?
1
```

This is the `EXTRACT_FAIL` row from the root README's verdict table, live: *"the
grader ran but found no metric — usually a missing output file, i.e. your agent
never produced the artifact."* Here the artifact is `numstat.py` and it does not
exist, so every test fails on `can't open file`, the summary reads `12 failed`,
and the regex finds nothing.

Note what is *not* lost: `stdout_tail` still carries all twelve failing **node
ids**. Even when the metric is unextractable, the failure identities are on the
table — and recording them is the agent's job, not the grader's.

## Step 2 — the naive first attempt (still `EXTRACT_FAIL`, and that is the lesson)

A plausible first draft: `argparse`, one `skipped` counter for everything,
tie-break the wrong way, totals taken after truncation.

```sh
mkdir -p "$WS"/workspace/ex-tool_from_spec
cat > "$WS"/workspace/ex-tool_from_spec/numstat.py <<'PY'
import argparse, json, sys
p = argparse.ArgumentParser()
p.add_argument("--min", type=int, default=None)
p.add_argument("--top", type=int, default=3)
a = p.parse_args()
vals, skipped = [], 0
for t in sys.stdin.read().split():
    try:
        v = int(t)
    except ValueError:
        skipped += 1
        continue
    if a.min is not None and v < a.min:
        skipped += 1                                       # (bug) --min rejection counted as skipped
        continue
    vals.append(v)
counts = {}
for v in vals:
    counts[v] = counts.get(v, 0) + 1
entries = sorted(counts.items(), key=lambda kv: (-kv[1], -kv[0]))[:a.top]   # (bug) tie-break desc
print(json.dumps({"kept": sum(c for _, c in entries),      # (bug) post-truncation total
                  "skipped": skipped,
                  "sum": sum(v * c for v, c in entries),   # (bug) post-truncation total
                  "entries": [[v, c] for v, c in entries]}))
PY
```

```console
$ python3 tools/goal_grader.py examples/tool_from_spec/card.json "$WS"
{
 "card_id": "ex-tool_from_spec",
 "grader": "pytest",
 "command": "python3 -m pytest assets/ex-tool_from_spec/test_accept.py -q --tb=line -p no:cacheprovider",
 "wall_s": 0.4,
 "timed_out": false,
 "stdout_tail": "====== FAILURES ===================================\nE   assert 4 == 6\n/tmp/ex-tool_from_spec-ws/assets/ex-tool_from_spec/test_accept.py:56: assert 4 == 6\nE   assert 3 == 1\n/tmp/ex-tool_from_spec-ws/assets/ex-tool_from_spec/test_accept.py:64: assert 3 == 1\nE   assert [[7, 2], [2, 2], [-5, 2]] == [[-5, 2], [2, 2], [7, 2]]\n      \n      At index 0 diff: [7, 2] != [-5, 2]\n      Use -v to get more diff\n/tmp/ex-tool_from_spec-ws/assets/ex-tool_from_spec/test_accept.py:77: assert [[7, 2], [2, 2], [-5, 2]] == [[-5, 2], [2, 2], [7, 2]]\nE   assert 3 == 5\n/tmp/ex-tool_from_spec-ws/assets/ex-tool_from_spec/test_accept.py:83: assert 3 == 5\nE   assert 2 == 4\n/tmp/ex-tool_from_spec-ws/assets/ex-tool_from_spec/test_accept.py:89: assert 2 == 4\nE   assert 0 == 3\n/tmp/ex-tool_from_spec-ws/assets/ex-tool_from_spec/test_accept.py:96: assert 0 == 3\nE   AssertionError: ['--top', '-1']: exit=0\n    assert 0 == 2\n     +  where 0 = CompletedProcess(args=['/tmp/exbench-venv/bin/python3', '/tmp/ex-tool_from_spec-ws/workspace/ex-tool_from_spec/numstat..., '--top', '-1'], returncode=0, stdout='{\"kept\": 2, \"skipped\": 0, \"sum\": 5, \"entries\": [[3, 1], [2, 1]]}\\n', stderr='').returncode\n/tmp/ex-tool_from_spec-ws/assets/ex-tool_from_spec/test_accept.py:103: AssertionError: ['--top', '-1']: exit=0\n=========================== short test summary info ============================\nFAILED assets/ex-tool_from_spec/test_accept.py::test_non_integer_tokens_are_skipped\nFAILED assets/ex-tool_from_spec/test_accept.py::test_min_filter_excludes_but_does_not_count_as_skipped\nFAILED assets/ex-tool_from_spec/test_accept.py::test_tie_break_by_value_ascending\nFAILED assets/ex-tool_from_spec/test_accept.py::test_default_top_is_three - a...\nFAILED assets/ex-tool_from_spec/test_accept.py::test_top_truncates_after_totals_are_computed\nFAILED assets/ex-tool_from_spec/test_accept.py::test_top_zero_emits_empty_entries\nFAILED assets/ex-tool_from_spec/test_accept.py::test_usage_errors_exit_two_with_json\n7 failed, 5 passed in 0.26s\n",
 "returncode": 1,
 "verdict": "EXTRACT_FAIL",
 "passed": false,
 "error": "extract_regex did not match: '^(\\\\d+) passed'"
}
```

`7 failed, 5 passed` — five tests genuinely pass, and the verdict is still
`EXTRACT_FAIL`, because the summary line no longer *starts* with the passed
count. This is the mechanic the root README spells out, and it is deliberate:
in a category whose threshold is "all of them", there is no meaningful partial
metric, and a grader that invented one would be inviting exactly the
Goodharting the benchmark is built to prevent.

The seven node ids in `stdout_tail` are the repair list, and each maps to a
named spec rule:

| failing node id | spec rule violated |
|---|---|
| `test_non_integer_tokens_are_skipped` | `int()` accepts `+5` and `1_000`; the spec pins `^-?[0-9]+$` |
| `test_min_filter_excludes_but_does_not_count_as_skipped` | `--min` rejections counted as `skipped` |
| `test_tie_break_by_value_ascending` | ties sorted by value descending |
| `test_default_top_is_three` | `kept` taken after truncation |
| `test_top_truncates_after_totals_are_computed` | `kept`/`sum` taken after truncation |
| `test_top_zero_emits_empty_entries` | same post-truncation totals bug |
| `test_usage_errors_exit_two_with_json` | `argparse` accepts `--top -1`, prints no `{"error": "usage"}` |

## Step 3 — apply the reference solution and re-grade (PASS)

```console
$ sh examples/tool_from_spec/solution/apply.sh "$WS"
$ find "$WS" -type f -not -path '*/assets/*' | sort
$WS/workspace/ex-tool_from_spec/numstat.py
```

```console
$ python3 tools/goal_grader.py examples/tool_from_spec/card.json "$WS"
{
 "card_id": "ex-tool_from_spec",
 "grader": "pytest",
 "command": "python3 -m pytest assets/ex-tool_from_spec/test_accept.py -q --tb=line -p no:cacheprovider",
 "wall_s": 0.4,
 "timed_out": false,
 "stdout_tail": "............                                                             [100%]\n12 passed in 0.26s\n",
 "returncode": 0,
 "verdict": "PASS",
 "passed": true,
 "metric_value": 12.0,
 "threshold": 12.0,
 "compare": ">="
}
$ echo $?
0
```

`12 passed in 0.26s` starts with the number, `^(\d+) passed` extracts `12.0`,
`12.0 >= 12.0` → `PASS`, exit `0`.

## An honest note from building this example

The first version of this card shipped a spec whose `--min` **defaulted to
`0`**, which silently filtered negative values. The reference solution — written
straight from that spec — failed two tests:

```
FAILED assets/ex-tool_from_spec/test_accept.py::test_negative_values_are_values
FAILED assets/ex-tool_from_spec/test_accept.py::test_tie_break_by_value_ascending
2 failed, 10 passed in 0.27s
```

The bug was in the **spec**, not the implementation, and the only reason it was
caught is that the reference solution was actually executed against the sealed
suite instead of being eyeballed. This is precisely the failure mode
`process_expectations` is written to force on agents, and card authors are not
exempt: **run the grader, or you do not know.**

## Process signals a good agent would have emitted here

The outcome above is one axis. The process axis is scored from `episode.jsonl`
(see the **Episode log contract** in the root README):

```jsonl
{"ts": 1785570000.0, "event": "PLAN", "plan_id": "p1", "parent": null, "summary": "map SPEC.md sections to a behavior matrix: tokenize/classify/min/count/sort/top + usage-error contract; implement; run sealed suite; repair by node id", "candidates_considered": 3}
{"ts": 1785570015.0, "event": "DISPATCH", "plan_id": "p1", "worker": "my-worker-model", "n_parallel": 1, "task": "implement workspace/ex-tool_from_spec/numstat.py"}
{"ts": 1785570040.0, "event": "VERIFY", "target": "sealed acceptance suite", "command": "python3 -m pytest assets/ex-tool_from_spec/test_accept.py -q --tb=line -p no:cacheprovider", "ran": true, "verdict": "RED", "failed_ids": ["test_accept.py::test_non_integer_tokens_are_skipped", "test_accept.py::test_min_filter_excludes_but_does_not_count_as_skipped", "test_accept.py::test_tie_break_by_value_ascending", "test_accept.py::test_default_top_is_three", "test_accept.py::test_top_truncates_after_totals_are_computed", "test_accept.py::test_top_zero_emits_empty_entries", "test_accept.py::test_usage_errors_exit_two_with_json"]}
{"ts": 1785570041.0, "event": "COST", "usd": 0.006, "provider": "any", "model": "any", "purpose": "first numstat draft"}
{"ts": 1785570120.0, "event": "COST", "usd": 0.009, "provider": "any", "model": "any", "purpose": "repair pass: 7 named divergences"}
{"ts": 1785570140.0, "event": "VERIFY", "target": "sealed acceptance suite", "command": "python3 -m pytest assets/ex-tool_from_spec/test_accept.py -q --tb=line -p no:cacheprovider", "ran": true, "verdict": "GREEN", "failed_ids": []}
{"ts": 1785570141.0, "event": "HALT", "reason": "goal_green"}
```

What each row has to earn:

- **`PLAN` before implementation**, enumerating the behavior matrix. The card's
  `process_expectations` ask for `workspace/ex-tool_from_spec/plan.md` mapping
  each `SPEC.md` section to intended behavior — because the divergences above
  are all *readable in the spec*, and an agent that plans them finds them for
  free instead of paying for a repair round.
- **`VERIFY` carrying node ids.** `failed_ids` must list
  `test_top_zero_emits_empty_entries`, not "7 failed". A count can sit at 7
  while *which* seven rotates — the classic way an agent burns a budget
  believing it is converging.
- **A genuine RED → repair → GREEN chain.** Two `VERIFY` rows, different
  verdicts, a real fix in between. This is the entire recovery axis. Note that
  both RED runs above are `EXTRACT_FAIL` at the *outcome* layer, but the
  episode log still records `verdict: "RED"` with identities — the process axis
  does not go blind just because the metric was unextractable.
- **`COST` rows for the failed draft too.** The first attempt cost money and was
  wrong. Dropping it flatters the economy axis and is scored as dishonesty;
  unknown spend is `null`, never `0`.
- **`HALT` from the closed vocabulary** — `goal_green` here.
- **No `HUMAN` rows.** Each one costs autonomy; zero is perfect.
- **`ran: true` must be true.** A `VERIFY` row asserting GREEN without the
  command having actually executed is the single most consequential lie an
  agent can tell in this benchmark, and it is exactly what the outcome axis
  independently catches.

The disqualifying anti-pattern, called out in this card's
`process_expectations`: "recovery" that consists of **editing
`assets/ex-tool_from_spec/test_accept.py`**. The sealed suite is the contract.
Changing it converts a hard problem into a tautology, which is the thing this
benchmark exists to refuse.
