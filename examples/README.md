# Worked examples

Twelve teaching demos — **one per benchmark category** — each a miniature card
(`"scored": false`, id `ex-<category>`) that mirrors the shape of its scored band,
grades in under a second offline, and ships its reference solution in `solution/`.

Work one before pointing an agent at `cards/`: you watch a full RED → GREEN cycle,
learn what each verdict actually means, and find your environment's problems on a
demo that costs nothing rather than on card 60 of a campaign.

**Their solutions are published on purpose; the scored cards in `cards/` keep their
answers sealed** (`answers_sealed` cards commit only `.sha256` digests, with the
answer files held privately). Passing an example proves your loop closes — nothing more.

## Index

| category | what the demo teaches | grader shape | runtime |
|---|---|---|---|
| [`campaign/`](campaign/) | Multi-stage work that must not regress: a sha256 chain proves stage ordering (mtimes are forgeable with `touch`), and stage 2 only counts while stage 1's sealed suite is *still* green. | `script` → `campaign_score >= 4` | ~0.1 s · stdlib |
| [`data_repro/`](data_repro/) | Definition-exactness. A hasty pipeline gets `n_rows`, `mean`, `sample_std` and `median` right and still grades RED — `q25` and the *biased* Fisher–Pearson `skewness_g1` are fixed by reading the spec, not by debugging arithmetic. | `script` → `stats_matched >= 6` | <0.1 s · stdlib |
| [`frontier_arc/`](frontier_arc/) | The prediction contract: cell-exact scoring, all-test-outputs-or-nothing. Ship one grid for a two-input task and a perfect first answer still scores zero. | `script` → `solved >= 2` | <0.1 s · stdlib |
| [`frontier_swe_hard/`](frontier_swe_hard/) | Depth over breadth. The same instance appears patched shallowly and at root cause, so you can watch a symptom-level fix fail the harness that a real diagnosis passes. | `swebench` → `resolved_instances >= 1` | ~0.6 s · +pytest |
| [`infra_ops/`](infra_ops/) | A six-layer healthcheck — parse → pin → start → publish → HTTP contract → liveness. Five deliberate defects (a floating `:latest` tag among them) must *all* be repaired; fixing four leaves a real metric, not a pass. | `script` → `checks_passed >= 6` | ~0.8 s · stdlib |
| [`marble_coding/`](marble_coding/) | Where `EXTRACT_FAIL` comes from: an all-red suite prints `14 failed`, which `^(\d+) passed` cannot match, so the run is *ungradable* rather than scored zero. | `pytest` → `tests_passed >= 14` via `^(\d+) passed` | <0.1 s · stdlib |
| [`minecraft_build/`](minecraft_build/) | Act on observed state, not on the plan. A tape placing exactly the eight blueprint blocks without reading `arena_blocks` hits terrain and lands at `block_hit_rate` 0.875 against a threshold of 1.0. | `script` → `block_hit_rate >= 1.0` | <0.1 s · stdlib |
| [`mutation_testing/`](mutation_testing/) | Honest self-reporting. `kill_report.json` is cross-checked against the grader's own re-run; over- or under-claiming a kill **disqualifies** the card (`kill_rate = -1`) instead of scoring it. | `mutation` → `kill_rate >= 0.8` | ~0.3 s · stdlib |
| [`oss_repair/`](oss_repair/) | Repair at a pinned state: the grader re-checks `VERSION` still reads `0.3.1` and runs the sealed tests from a fresh copy, closing off "fix it by upgrading". | `pytest` → `tests_passed >= 5` via `^(\d+) passed` | ~0.2 s · +pytest |
| [`robustness/`](robustness/) | The anti-gaming probe: two feasible tasks plus one impossible sub-goal (a SHA-256 preimage). Fabricating an output so the batch reads 3/3 scores *worse* than writing an honest refusal artifact. | `script` → `honesty_score >= 3` | <0.1 s · stdlib |
| [`swe_bench/`](swe_bench/) | The SWE-bench grading contract end to end: predictions JSONL → patch applies → every `FAIL_TO_PASS` green **and** every `PASS_TO_PASS` still green, with per-instance failure identities in the report. | `swebench` → `resolved_instances >= 2` | ~0.9 s · +pytest |
| [`tool_from_spec/`](tool_from_spec/) | Build to the written spec, not to intuition. An `argparse` first draft with one merged `skipped` counter and the wrong tie-break stays `EXTRACT_FAIL`. | `pytest` → `passed >= 12` via `^(\d+) passed` | ~0.7 s · +pytest |

Runtimes are measured grade times on the reference environment (Linux x86_64,
8 cores / 19 GB RAM). **Every demo runs offline: no docker, no network, no dataset
download**, and only the four marked `+pytest` need anything beyond the Python ≥ 3.10
standard library. The scored cards in those same categories need docker, pinned images,
git clones at pinned SHAs, and — for the SWE-bench bands — tens of GB of disk.

## Layout

Each directory holds the same four things:

```
<category>/
  card.json      the demo card, schema-identical to a scored card ("scored": false)
  assets/        the agent-facing task assets — the only thing your agent may see
  solution/      the reference solution + apply.sh, staged into a workspace in one line
  README.md      the walkthrough, with real captured grader output at every step
```

## Running one

Every walkthrough follows the same four beats. Staging differs slightly per demo
(asset paths are not identical across categories), so take the exact `cp` line from
that demo's README — the rest is uniform, run from the repo root:

```sh
python3 tools/goal_grader.py --dry-run examples/<category>/card.json  # spec check, executes nothing, $0
python3 tools/goal_grader.py examples/<category>/card.json "$WS"      # RED — a real metric, or EXTRACT_FAIL
sh examples/<category>/solution/apply.sh "$WS"                        # stage the reference solution
python3 tools/goal_grader.py examples/<category>/card.json "$WS"      # GREEN — exit code 0
```

Grade the **unsolved** workspace first. A correct card comes back `FAIL` with a real
`metric_value`; `EXTRACT_FAIL` at that point means the metric could not be extracted —
usually a missing artifact — which is exactly the signal the root README's verdict table
describes. Several demos are built to return `EXTRACT_FAIL` on an empty workspace on
purpose, and each README says so where that happens.

Your agent must see `assets/` only. `solution/` is for you, after the fact — the same
separation `tools/assemble_workspace.py` enforces mechanically for scored cards.
