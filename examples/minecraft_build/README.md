# Worked example — `minecraft_build`

A **teaching example**, not a benchmark card. `card.json` here carries
`"scored": false` and its own reference solution ships in `solution/`. It exists
so you can watch a `minecraft_build` card go RED → GREEN end to end without
standing up a Minecraft server.

| | scored cards (gc-360 … gc-371) | this example |
|---|---|---|
| world | Minecraft 1.19.2 in docker (`itzg/minecraft-server`), fresh flat world per run | a simulated arena inside `assets/ex-minecraft_build/judger.py` |
| bots | mineflayer over Node 20, pinned npm packages | an action tape the agent writes, replayed by the judger |
| judge | MARBLE `build_judger` at a pinned SHA | the same judger interface, miniature |
| score file | `.../result/<task>/score.json` with `block_hit_rate`, `view_hit_rate`, `efficiency` | identical keys, identical grader command shape |
| wall time | many minutes, docker + Node + npm | **< 1 s**, python3 stdlib only |

What survives the shrink is everything that made the card hard: blueprint-relative
coordinates you must translate through `map.json`, a material chest with an exact
stock, arena terrain that already occupies one of your cells, directional blocks,
and the two honest ledgers without which the judger refuses to write a score at all.

---

## 0. Set up a workspace

```sh
WS="${TMPDIR:-/tmp}/ws-ex-minecraft_build"
mkdir -p "$WS" && cp -a examples/minecraft_build/assets "$WS"/
```

```console
$ python3 tools/goal_grader.py --dry-run examples/minecraft_build/card.json
{"card": "examples/minecraft_build/card.json", "spec_ok": true, "problems": []}
```

## 1. Grade the empty workspace — `EXTRACT_FAIL`

```console
$ python3 tools/goal_grader.py examples/minecraft_build/card.json "$WS"
{
 "card_id": "ex-minecraft_build",
 "grader": "script",
 "command": "python3 -c \"import json;d=json.load(open('work/ex-minecraft_build/result/ex-minecraft_build/score.json'));print(json.dumps({'block_hit_rate':float(d['block_hit_rate']),'view_hit_rate':float(d['view_hit_rate']),'efficiency':float(d['efficiency'])}))\"",
 "wall_s": 0.0,
 "timed_out": false,
 "stdout_tail": "",
 "returncode": 1,
 "verdict": "EXTRACT_FAIL",
 "passed": false,
 "error": "metric 'block_hit_rate' not found in stdout"
}
```

Note the verdict: **not** `FAIL`. There is no score file yet, so the grader could
not extract a metric — and an ungradable run is never a pass. This is the single
most common first-run verdict in practice, and it almost always means the same
thing: *the agent never produced the artifact*. `EXTRACT_FAIL` is a statement
about the workspace, not about the card.

## 2. Prepare the arena (the judger's setup phase)

```console
$ python3 assets/ex-minecraft_build/judger.py prepare --task ex-minecraft_build --idx 0 --agent_names builder_a
arena ready: 'Cobble Kiln Cairn', 8 target blocks, chest at [-4, -60, 0] stocked {"furnace": 1, "oak_log": 1, "stone_bricks": 6}
pre-existing arena blocks (scan before you place): [{"pos": [0, -60, 1], "name": "dirt"}]
world coordinates written to work/ex-minecraft_build/data/map.json
```

`prepare` is what `docker compose up` + the MARBLE judger launch do on the scored
cards: fresh world, blueprint shifted into world space, chest stocked, and
`.cache/load_status.cache` flipped to `loaded`. It publishes the only coordinates
that matter:

```console
$ python3 -c "import json; m=json.load(open('work/ex-minecraft_build/data/map.json')); \
print('chest', m['chest'], m['chest_stock']); print('arena', m['arena_blocks']); \
[print('target', t['pos'], t['name'], 'facing', t['facing']) for t in m['targets']]"
chest [-4, -60, 0] {'stone_bricks': 6, 'furnace': 1, 'oak_log': 1}
arena [{'pos': [0, -60, 1], 'name': 'dirt'}]
target [0, -60, 0] stone_bricks facing A
target [0, -60, 1] stone_bricks facing A
target [1, -60, 0] stone_bricks facing A
target [1, -60, 1] stone_bricks facing A
target [2, -60, 0] stone_bricks facing A
target [2, -60, 1] stone_bricks facing A
target [0, -59, 0] furnace facing W
target [2, -59, 1] oak_log facing x
```

Running the judger before there is anything to judge is refused, not scored:

```console
$ python3 assets/ex-minecraft_build/judger.py run --task ex-minecraft_build --idx 0 --agent_names builder_a
judger refuses to score this run: build plan missing: work/ex-minecraft_build/data/build_plan.json
score.json was NOT written (fail-closed)
```

## 3. First attempt: a tape written from the blueprint alone — RED with a metric

The blueprint says eight blocks; a plan that places exactly those eight and never
reads `arena_blocks` looks complete and is not. (Reproduce it by dropping the
`break` action from the reference tape.)

```console
$ python3 assets/ex-minecraft_build/judger.py run --task ex-minecraft_build --idx 0 --agent_names builder_a
plan error: action 4: [0, -60, 1] is occupied by dirt -- break it first
mismatch: [0, -60, 1] expected stone_bricks, observed dirt
{"block_hit_rate": 0.875, "view_hit_rate": 1.0, "efficiency": 2.8, "end_reason": "plan_exhausted"}

$ python3 tools/goal_grader.py examples/minecraft_build/card.json "$WS"
{
 "card_id": "ex-minecraft_build",
 "grader": "script",
 "command": "python3 -c \"import json;d=json.load(open('work/ex-minecraft_build/result/ex-minecraft_build/score.json'));print(json.dumps({'block_hit_rate':float(d['block_hit_rate']),'view_hit_rate':float(d['view_hit_rate']),'efficiency':float(d['efficiency'])}))\"",
 "wall_s": 0.0,
 "timed_out": false,
 "stdout_tail": "{\"block_hit_rate\": 0.875, \"view_hit_rate\": 1.0, \"efficiency\": 2.8}\n",
 "returncode": 0,
 "verdict": "FAIL",
 "passed": false,
 "metric_value": 0.875,
 "threshold": 1.0,
 "compare": ">="
}
```

`0.875` = 7 of 8. The threshold is `1.0`: seven eighths of a build is worth
exactly as much as zero. What makes this recoverable is the **identity** the
judger hands back — `[0, -60, 1] expected stone_bricks, observed dirt` — a
coordinate, an expectation and an observation, not a count.

## 4. Apply the reference solution and re-run the judger

`apply.sh` drops the deliverables in and then replays the tape through the
judger — the score file is the sealed judger's output, never something a
solution ships by hand. (It also runs `prepare` first if you skipped step 2, so
the script works on a bare assets-only workspace too.)

```console
$ sh examples/minecraft_build/solution/apply.sh "$WS"
{"block_hit_rate": 1.0, "view_hit_rate": 1.0, "efficiency": 3.2, "end_reason": "task_complete"}
```

The solution is exactly what an agent must produce, nothing else:

| file | why the judger needs it |
|---|---|
| `work/ex-minecraft_build/data/build_plan.json` | the action tape: withdraw → **break the dirt** → 6 floor blocks → furnace facing `W` → oak_log axis `x` |
| `work/ex-minecraft_build/data/action_log.json` | per-phase intervals; `efficiency` is the union of them |
| `work/ex-minecraft_build/data/tokens.json` | the spend ledger |
| `work/ex-minecraft_build/placement_plan.md` | the plan artifact the card's `process_expectations` require before the first block |

## 5. Grade again — GREEN

```console
$ python3 tools/goal_grader.py examples/minecraft_build/card.json "$WS"
{
 "card_id": "ex-minecraft_build",
 "grader": "script",
 "command": "python3 -c \"import json;d=json.load(open('work/ex-minecraft_build/result/ex-minecraft_build/score.json'));print(json.dumps({'block_hit_rate':float(d['block_hit_rate']),'view_hit_rate':float(d['view_hit_rate']),'efficiency':float(d['efficiency'])}))\"",
 "wall_s": 0.0,
 "timed_out": false,
 "stdout_tail": "{\"block_hit_rate\": 1.0, \"view_hit_rate\": 1.0, \"efficiency\": 3.2}\n",
 "returncode": 0,
 "verdict": "PASS",
 "passed": true,
 "metric_value": 1.0,
 "threshold": 1.0,
 "compare": ">="
}
```

And the judger's own snapshot feed has kept both readings — the record the
process axis reads for the recovery chain:

```json
[
 {"ts": "2026-08-02 08:05:44", "block_hit_rate": 0.875, "view_hit_rate": 1.0,
  "mismatches": ["[0, -60, 1] expected stone_bricks, observed dirt"], "strays": []},
 {"ts": "2026-08-02 08:05:50", "block_hit_rate": 1.0, "view_hit_rate": 1.0,
  "mismatches": [], "strays": []}
]
```

---

## What the grader actually measured

The success command is deliberately dumb: it opens
`work/ex-minecraft_build/result/ex-minecraft_build/score.json`, prints three
numbers as one JSON line, and the grader reads `block_hit_rate` out of it and
compares to `1.0`. All of the judgment lives in the sealed judger that wrote that
file — the same split as the scored cards, where the grader command only reads
MARBLE's `score.json`.

Which is why the honest-ledger gate matters. The judger recomputes every
`duration` from its own interval and refuses inconsistent ledgers outright:

```console
$ python3 assets/ex-minecraft_build/judger.py run --task ex-minecraft_build --idx 0 --agent_names builder_a
judger refuses to score this run: action ledger 'builder_a' entry 2 claims duration 900 s but the interval 2026-08-02 09:01:10..2026-08-02 09:02:30 is 80 s
score.json was NOT written (fail-closed)
```

(captured after padding the third ledger entry from 80 s to 900 s). No score file
is written, so the card grades `EXTRACT_FAIL` — **a padded ledger cannot buy a
pass, it can only lose one.** And because `efficiency` is blocks per *active*
minute, even a consistent-but-inflated ledger lowers the number it was inflated
to raise.

## What good process would have looked like here

Episode-log shape for this card (see the root README for the contract) —
**illustrative, not a captured run**:

```jsonl
{"event":"PLAN","plan_id":"p1","summary":"prepare arena, read map.json, survey arena_blocks, order placements floor->directional","candidates_considered":3}
{"event":"VERIFY","target":"arena","command":"cat work/ex-minecraft_build/.cache/load_status.cache","ran":true,"verdict":"GREEN","failed_ids":[]}
{"event":"DISPATCH","plan_id":"p1","worker":"builder_a","n_parallel":1,"task":"place 8 blocks from data/map.json"}
{"event":"VERIFY","target":"scan 1","command":"judger.py run --task ex-minecraft_build","ran":true,"verdict":"RED","failed_ids":["[0,-60,1] expected stone_bricks, observed dirt"]}
{"event":"COST","usd":0.02,"purpose":"plan + repair + verify"}
{"event":"VERIFY","target":"scan 2","command":"judger.py run --task ex-minecraft_build","ran":true,"verdict":"GREEN","failed_ids":[]}
{"event":"HALT","reason":"goal_green"}
```

- **planning** — the `PLAN` precedes any placement and names the survey step. The
  whole difficulty of this card is that the blueprint is *not* the world;
  a plan that never mentions `map.json` has already lost the 8th block.
- **verification** — `VERIFY` events that actually ran, with `failed_ids` carrying
  the mismatched **coordinate**. "1 block short" would be useless; `[0,-60,1]
  expected stone_bricks, observed dirt` is directly actionable.
- **recovery** — the RED scan → repair → GREEN scan chain, mirrored on disk by the
  two snapshots in `data/score.json`.
- **honesty** — `COST` rows match `tokens.json`, and the action ledger matches the
  wall clock. Here honesty is not merely scored, it is *enforced*: the judger is
  the mechanism.
- **autonomy** — zero `HUMAN` events; `HALT: goal_green` from the closed vocabulary.
- **economy** — Σ`COST` against `budget_usd: 0.25`.

`DISPATCH` appears with `n_parallel: 1` because one bot is the right shape for
eight blocks. The scored multi-bot cards (gc-364 twin towers, gc-369 three-bot
bastion) are where parallel dispatch stops being decoration.

## Running the real thing

```sh
python3 tools/goal_grader.py --dry-run cards/gc-360_stone_podium_exact_build.json
```

That card needs docker (`itzg/minecraft-server:2024.6.1-java17`), Node 20, four
pinned npm packages and a MARBLE clone at a pinned SHA, and it follows
`cards/assets/gc-360/RUNBOOK.md` — which is the document
`assets/ex-minecraft_build/RUNBOOK.md` is modelled on, phase for phase.
