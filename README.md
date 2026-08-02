# AGI_BENCHMARK

A benchmark for **long-horizon agent systems** that scores the **process** —
plan → verify → execute → re-verify — from machine-readable logs, alongside a
fail-closed, machine-graded outcome.

**Dashboard / card browser:**
[muhan97-coder.github.io/AGI_BENCHMARK](https://muhan97-coder.github.io/AGI_BENCHMARK/)
(served from [`docs/`](docs/) via GitHub Pages; or open `docs/index.html`
locally in a browser — it is fully self-contained).

## Why process-first

Most agent benchmarks grade only the final artifact. But an agent can be right
for the wrong reasons (lucky pass, silent error swallowing) and wrong for the
right ones (a sound loop that honestly refuses an impossible goal). This
benchmark treats them differently:

1. **Outcome is a separate axis.** Every card has a sealed, machine-checkable
   success criterion (numeric threshold on a command's output). No LLM judges.
2. **Process is scored from logs only.** Six axes — planning, verification,
   honesty, recovery, autonomy, economy — computed from execution logs, never
   from the agent's self-report.
3. **Anti-Goodhart by construction.** Cards are preregistered before runs;
   graders are fail-closed (an ungradable run is a failure, never a pass);
   unknown values are recorded as unknown, never as zero.

## Repository layout

```
cards/           155 scored goal cards (JSON) + cards/assets/<id>/ card assets
cards/INDEX.md   full card index with categories and difficulty
examples/        12 teaching demos (one per category) WITH published solutions
tools/goal_grader.py       the machine grader (stdlib only, fail-closed)
tools/assemble_workspace.py builds an agent workspace from task assets only
tools/restore_sealed.py    grader-side restore of sealed answer files
tools/build_dashboard.py   rebuilds docs/index.html from cards/
docs/index.html  static dashboard (card browser + leaderboard)
results/leaderboard.json leaderboard entries (submit via PR)
```

## Quick start

```sh
CARD=cards/gc-300_swebench_single_django.json

# 1. validate the card's grader spec (no execution, $0)
python3 tools/goal_grader.py --dry-run "$CARD"

# 2. build the agent-facing workspace (task assets only, no answer files)
python3 tools/assemble_workspace.py "$CARD" /tmp/ws-gc-300

# 3. point YOUR agent at /tmp/ws-gc-300 and let it pursue the card's goal,
#    then grade whatever it produced
python3 tools/goal_grader.py "$CARD" /tmp/ws-gc-300
```

Grade from a workspace, never from a checkout of this repository: the graders
read relative paths, and a card whose answers are sealed will not grade
correctly against the repo itself.

A card is a sealed contract: `goal` (what the agent must achieve), `budget_usd`
(spend envelope), `success_criteria.spec` (the grading command + numeric
threshold), and `process_expectations` (what observable good process looks
like).

`budget_usd` is a **model-agnostic ceiling, not a target**. It is set by
horizon — `1d` ≤ $100, `3d` ≤ $250, `1w` ≤ $600, `1m` ≤ $2000 — sized so that a
frontier-priced model (tens of dollars per million output tokens) can plan,
retry, and verify repeatedly without the envelope being the thing that stops
it. A cheap model will typically finish two orders of magnitude under the
ceiling; that is the expected outcome, not an anomaly. The economy axis scores spend *per verified unit of
progress*, so undershooting the ceiling is rewarded and burning it without
progress is not.

All resources a card cites are public and pinned (git SHAs, package versions,
docker tags); everything else ships in `cards/assets/`.

## Environment

Grading is the easy part — the environment is the boss fight. What you need,
by card category:

| categories | requirements |
|---|---|
| `data_repro`, `tool_from_spec`, `frontier_arc`, `robustness`, `campaign` | Python ≥ 3.10 plus each card's pinned pip deps (`data_repro` cards pin numpy / pandas / scipy) |
| `mutation_testing`, `oss_repair`, `marble_coding` | + git clones at pinned SHAs, pinned pip packages (`mutmut` for the mutation band) |
| `infra_ops`, `minecraft_build` | + Docker & docker compose (pinned images; `minecraft_build` also needs Node 20 + pinned npm packages) |
| swe_bench, frontier_swe_hard | + the swebench docker harness — **heavy**: several GB of images *per instance environment*; budget 50 GB+ of disk for the larger batches |

The `minecraft_build` cards are attemptable by anyone: the mineflayer access
layer they need ships in this repo at
[`examples/minecraft_build/bridge/`](examples/minecraft_build/bridge/) — a hand,
not a brain (see *What we ship and what we don't*).

**Reference environment** (what the baseline runs on): Linux x86_64 (a WSL2
VM, nothing exotic), 8 cores / 19 GB RAM, Docker 24+, Python 3.10, Node 20.
The grader itself (`tools/goal_grader.py`) is stdlib-only.

**Setup pitfalls we actually hit** (so you don't):

- A native PostgreSQL already squatting on `5432` silently breaks container
  DB cards — remap container ports, don't fight the host.
- Unpinned image tags drift (`postgres` pulled 18 against data written by 12).
  Every image in these cards is tag-pinned for a reason.
- A stray empty `tests/` directory higher up your path can shadow a package
  under pytest's rootdir rules and produce phantom failures — run graders from
  the repo root.
- `__pycache__/` embeds absolute build paths; if you fork this benchmark,
  keep compiled artifacts out of your assets.
- Concurrent cards that bind host ports (infra, minecraft) must not run in
  parallel with each other — serialize those categories, parallelize the rest.

## Smoke first, campaign second (recommended)

Before committing a multi-day run, probe **one card per category** — the
failure you find will almost always be environmental, and finding it on card 1
instead of card 60 is the difference between an afternoon and a week.

```sh
# 1. Does the environment have what these cards need?
docker info >/dev/null && echo "docker ok"
python3 -c "import swebench; print('swebench ok')"      # swe_bench / frontier_swe_hard
node -e "require('mineflayer'); console.log('mineflayer ok')"   # minecraft_build

# 2. Are the specs well-formed? (no execution, $0)
for c in cards/gc-*.json; do
  python3 tools/goal_grader.py --dry-run "$c" | grep -q '"spec_ok": true' || echo "BAD SPEC: $c"
done

# 3. Does the grading loop close end-to-end? Run a worked example: it walks
#    an unsolved workspace (RED) to a solved one (PASS) offline in ~1 s.
WS="${TMPDIR:-/tmp}/ws-ex-data_repro"
mkdir -p "$WS/assets" && cp -r examples/data_repro/assets/ex-data_repro "$WS/assets/"
python3 tools/goal_grader.py examples/data_repro/card.json "$WS"   # RED, with a metric
sh examples/data_repro/solution/apply.sh "$WS"
python3 tools/goal_grader.py examples/data_repro/card.json "$WS"   # PASS

# 4. Then try one *scored* card per category you plan to run — on a workspace
#    built by assemble_workspace.py. An unsolved scored card must come back
#    RED with a real metric value, not EXTRACT_FAIL.
```

Read the verdict of that last step carefully:

| result | meaning |
|---|---|
| `FAIL` with a `metric_value` | the card works — your agent simply hasn't done the work yet |
| `EXTRACT_FAIL` | the grader ran but found no metric — usually a missing output file, i.e. **your agent never produced the artifact**. Check that your agent can actually write files and run commands before blaming the card |
| `SPEC_INVALID` | the card is malformed — please open an issue |
| `TIMEOUT` | raise the timeout, or the environment is missing something the command waits on |

The `EXTRACT_FAIL` row is worth internalizing: in our own first run it was the
single most common outcome, and the cause was not the benchmark — it was an
agent that planned and verified diligently but never invoked its own execution
channel. That is exactly the kind of gap the process axis is meant to expose.

## Worked examples

[`examples/`](examples/) holds **one teaching demo per category — all twelve** —
each a miniature card built to the same schema, graded by the same
`tools/goal_grader.py`, and shipped *with* its reference solution in
`solution/`. They carry `"scored": false` and ids of the form `ex-<category>`:
they are not part of the benchmark, and passing one proves only that your loop
closes.

Publishing solutions is the whole point of that directory, and the reason the
scored cards in `cards/` do the opposite: a scored card's answers stay sealed
(`answers_sealed` cards commit only `.sha256` digests), because publishing them
would destroy them. So the demos are where you learn the contract, and `cards/`
is where you are measured against it.

Every demo runs **offline in about a second** — no docker, no network, no
dataset download; Python ≥ 3.10, plus `pytest` for the three `grader: pytest`
demos. Each walks the
same four beats with real captured output at every step: validate the spec,
grade the unsolved workspace RED, apply the reference solution, grade GREEN.
Between them they exercise all four grader shapes in the benchmark — `script`,
`pytest`, `mutation`, `swebench` — and the three verdicts you actually meet in a
run: `FAIL` with a real metric, `PASS`, and the `EXTRACT_FAIL` traps, several of
them planted deliberately so you can see what causes one.

```sh
# the cheapest possible smoke test: a full RED -> GREEN cycle, $0, ~1 s
WS="${TMPDIR:-/tmp}/ws-ex-swe_bench"
mkdir -p "$WS/assets" && cp -r examples/swe_bench/assets "$WS/assets/ex-swe_bench"

python3 tools/goal_grader.py examples/swe_bench/card.json "$WS"   # -> EXTRACT_FAIL: no predictions yet
sh examples/swe_bench/solution/apply.sh "$WS"
python3 tools/goal_grader.py examples/swe_bench/card.json "$WS"   # -> PASS, resolved_instances 3 >= 2
```

Start with [`examples/README.md`](examples/README.md) — it indexes all twelve
with what each one teaches, its grader shape, and its measured runtime.

## Categories

SWE-bench (pinned Lite instances) · OSS repair at pinned SHAs · mutation
testing · Minecraft builds on fresh docker worlds · infra/ops tuning in docker ·
deterministic data reproduction · tool-from-spec with sealed acceptance tests ·
multi-stage campaigns · robustness/anti-gaming probes · MARBLE coding tasks ·
**frontier**: ARC-AGI-2 abstract reasoning · SWE-bench Verified (hard).

## Grading output (outcome axis)

`tools/goal_grader.py` prints one JSON object — the verdict **plus the evidence
to reproduce it**:

```json
{
 "card_id": "ex-data_repro", "grader": "script",
 "command": "python3 assets/ex-data_repro/grade.py",
 "wall_s": 0.1, "timed_out": false, "returncode": 0,
 "stdout_tail": "...{\"stats_matched\": 6}",
 "verdict": "PASS", "passed": true,
 "metric_value": 6.0, "threshold": 6.0, "compare": ">="
}
```

`verdict` is one of:

| verdict | meaning | passed |
|---|---|---|
| `PASS` / `FAIL` | metric extracted, compared against threshold | true / false |
| `SPEC_INVALID` | card spec malformed — nothing was executed | always false |
| `EXTRACT_FAIL` | command ran but the metric could not be extracted | always false |
| `TIMEOUT` | command exceeded the time limit | always false |

Fail-closed by construction: there is no code path where an ungradable run
passes. Exit code is `0` only for `PASS`.

Metric extraction, in priority order: `metric: "exit_code"` uses the return
code; `extract_regex` takes capture group 1 from stdout; otherwise the **last
JSON line** of stdout must contain `metric` as a key. A failing pytest run
prints `"N failed, M passed"`, which regex `^(\d+) passed` does not match →
`EXTRACT_FAIL` → red, mechanically.

## Episode log contract (process axis — v1 draft)

The process axes are computed from an **episode log**: one JSONL file
(`episode.jsonl`) the agent system emits while pursuing a card. This contract
is architecture-neutral — a single-agent loop, a 100-way parallel planner, or
an orchestrated swarm all project onto the same six event types:

```jsonl
{"ts": 1785570000.0, "event": "PLAN",     "plan_id": "p1", "parent": null, "summary": "split goal into 3 stages", "candidates_considered": 16}
{"ts": 1785570010.0, "event": "DISPATCH", "plan_id": "p1", "worker": "my-worker-model", "n_parallel": 100, "task": "stage 1"}
{"ts": 1785570100.0, "event": "VERIFY",   "target": "stage 1", "command": "pytest -q tests/", "ran": true, "verdict": "RED", "failed_ids": ["tests/test_x.py::test_y"]}
{"ts": 1785570110.0, "event": "COST",     "usd": 0.0021, "provider": "any", "model": "any", "purpose": "stage 1 attempt"}
{"ts": 1785570200.0, "event": "HUMAN",    "note": "operator gave a hint"}
{"ts": 1785570300.0, "event": "HALT",     "reason": "goal_green"}
```

Rules that make the axes meaningful:

- **VERIFY must carry failure *identities*** (`failed_ids`), not counts — a
  count can stay constant while the failures rotate.
- **COST rows must be honest**: every billable call gets a row, including
  failed calls (`usd` may be 0 only if the call was actually free).
- **HALT reasons are closed-vocabulary**: `goal_green`, `budget_exhausted`,
  `max_attempts`, `refused_impossible` (the honest answer to an impossible
  goal), `error`.
- **HUMAN events count against autonomy.** Zero is a perfect score.
- Unknown is `null`, never `0` — a scorer must be able to distinguish "cheap"
  from "unmeasured".

Six axes, all mechanical: **planning** (PLAN structure and candidate breadth),
**verification** (VERIFY ran-rate and identity tracking), **honesty** (COST
completeness, HALT truthfulness), **recovery** (RED → repair → GREEN chains),
**autonomy** (HUMAN count, envelope self-stops), **economy** (Σ COST vs
`budget_usd`). The reference scorer for this contract ships in v1.0; per-card
outcome grading works today without it.

## Leaderboard submission

Add one entry to `results/leaderboard.json` by PR:

```json
{"agent": "my-agent v1", "submitted": "2026-08-01",
 "models": {"planner": "some-frontier-model", "worker": "some-cheap-model",
            "reviewer": "a-third-model"},
 "cards_attempted": 155, "outcome_pass": "41/155",
 "process": {"planning": 0.8, "verification": 0.9, "honesty": 1.0,
             "recovery": 0.6, "autonomy": 1.0, "economy": 0.7},
 "shared_tooling": ["mc_bridge"],
 "usd": 12.4, "logs": "https://link-to-your-episode-logs"}
```

Every number must be backed by attached grader outputs and episode logs —
entries are verified by re-running the sealed graders before merge.

`shared_tooling` is **optional** and lists which pieces of the repository's
public plumbing the run used (`mc_bridge` today; more as categories are added).
It is a fairness label, not a penalty: shared plumbing is published precisely so
that everyone may use it, and an entry that used it is not discounted. It exists
so two entries can be compared knowing whether one also built its own access
layer — and so a category's plumbing can be revised without silently
invalidating older entries. Omit the field if you used none.

`models` is free-form: name whichever models filled whichever role. Mixed-model
systems are first-class here — spend is the only cross-architecture unit that
means the same thing for everyone, so routing cheap work to cheap models and
reserving expensive ones for hard decisions shows up as a *higher* economy
score, not as a caveat.

**Trust tiers** (logs are self-emitted and therefore forgeable — the tier says
how hard we checked):

| tier | what it means |
|---|---|
| `self-reported` | logs submitted as-is; outcome re-graded, process taken on trust |
| `replay-verified` | VERIFY events carry a `workspace_ref` (git SHA); we sample events and re-run their commands at that state — failure identities must reproduce or the entry is rejected |
| `harness-run` | the agent ran inside the benchmark harness, which emits the logs itself — the agent never touches its own telemetry |

`workspace_ref` on VERIFY events is required for anything above
`self-reported`. Fabricating a replay-verified log means fabricating repo
states where the claimed failures actually reproduce — the cost of forgery
rises to the cost of doing the work.

## What we ship and what we don't

One rule, and it decides every publish/withhold question in this repository:

> **Environment access is public. Task strategy is private.**

**Public — the plumbing that reaches the environment.** The docker grading
harness, the Minecraft bridge
([`examples/minecraft_build/bridge/`](examples/minecraft_build/bridge/)), the
workspace assembler, the runbooks and pinned compose files. None of it is the
thing being measured; it is the precondition for measuring at all. Writing a
mineflayer transport or a container harness is a tax paid in engineering hours
that says nothing about agent capability, and a category where only the authors
own the plumbing produces scores nobody should trust — including ours. If
reaching the environment is hard in a way that has nothing to do with the task,
that difficulty is our problem to remove, not your score to lose.

**Private — the strategy that solves the task, and the answers that grade it.**
Plan decomposition, placement ordering, mismatch detection, repair loops,
verification policy: these are the six process axes wearing different clothes,
and shipping any of them would mean the benchmark scoring its own code. Grading
answers stay sealed for the ordinary reason — publishing them destroys the card
(see *Contamination & leakage* below, and the `answers_sealed` pack).

The line between the two is drawn by one question: *would shipping this make a
scored behaviour disappear from the log?* A bridge that only reports
`TARGET_OCCUPIED` leaves the decision — and the evidence of the decision —
with the agent. A bridge that quietly broke the offending block would delete
the recovery axis for everyone.

**This rule applies to every category added from here on** — robotics,
infrastructure, whatever comes next. The access layer for a new environment
ships with it, on the same terms: enough to reach the world, never enough to
decide what to do in it. When we cannot publish an access layer (licensed
hardware, a private endpoint), that category is marked as such rather than
scored as if the field were level.

## Contamination & leakage

Honesty about what a score means (v1.0-beta):

- Every card carries `contamination_risk`:
  **`public_gold_exists`** (53 cards — SWE-bench gold patches are in the public
  dataset; OSS-repair fixes may exist in upstream history past the pinned SHA),
  **`answers_sealed`** (15 cards — the grader's answer files are **not in this
  repository**; only `<name>.sha256` commitments are. The sealed pack is held
  privately by the maintainers), **`low`** (87 cards — visible sealed
  tests/blueprints are the *spec*, not the answer; hard-coding-to-tests is
  countered by the mutation and robustness bands).
- **Oracle isolation** (shipped, enforced):
  - `tools/assemble_workspace.py <card> <dest>` builds the agent-facing
    workspace from task assets only — point your agent there, never at this
    repo, and answer files are structurally out of reach.
  - Grading `answers_sealed` cards requires the sealed pack:
    `tools/restore_sealed.py --sealed-dir <pack>` restores the files and
    verifies each against its committed sha256 (mismatch aborts). Request the
    pack via an issue, or submit runs for maintainer-side grading.
- The process axis is itself a leak detector: an outcome PASS with an empty
  process trace (no verification runs, near-zero spend, implausibly short wall
  time) is mechanically flaggable as a suspicious shortcut — something an
  outcome-only benchmark cannot see.

## Status

**v1.0-beta.** Frontier band added: 12 ARC-AGI-2 + 12 SWE-bench Verified (hard) cards, reported separately on the leaderboard (raw problem-solving depth vs loop quality). Cards are generated and machine-validated (spec dry-runs, live
pin checks, portability sweep) but the preregistered *sealed* set will be
tagged as `v1.0` after review. The neutral episode-log contract — which lets
any agent system be scored on the process axes via a thin adapter — is the main
v1 work item; the reference scorer for it is not published yet, so today the
repository grades outcomes and specifies the process contract without scoring it
for you. The first baseline (`agent-one`, a self-improving loop on a budget
worker model, `harness-run` tier) is mid-measurement; its numbers will appear on
the leaderboard when the run completes.

## License

MIT — see [LICENSE](LICENSE).
