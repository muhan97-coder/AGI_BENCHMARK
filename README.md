# AGI_BENCHMARK

> ## ⚠️ All released versions are withdrawn (2026-08-04)
>
> **`v1.0-alpha`, `v1.0-beta`, and `v2-alpha` are withdrawn and their tags have
> been removed.** Do not use them to evaluate an agent or to report a number.
> No replacement tag exists yet.
>
> Two independent problems, either of which is enough on its own:
>
> **1 — The v1 tags never measured an agent.** Reconstructing our own 26-episode
> ledger showed that no episode ever ended by exhausting its budget: 10 ended on
> the wall clock, 8 on the cycle cap (every one at exactly 3 cycles), 2 on
> consecutive failures, 0 on budget. That was arithmetic, not luck — a cycle cap
> of 3, at our most expensive $0.0915 per cycle, permits $0.27, and the smallest
> card budget in the set is $0.50. The budget was not unreached, it was
> **unreachable**. Every verdict was a statement about our runner's limits.
>
> **2 — Most cards cannot be moved by an agent's honest work.** A read-only
> audit of all 155 public cards (2026-08-02) classified 90 as unable to move
> their own metric except by forgery, 24 as measuring "can you rewrite the
> tests", 20 as unverified one-shots, and **21 as responding honestly to what an
> agent does inside the sandbox**. Since then we have found and fixed part of the
> cause (a broken DNS symlink in our sandbox killed `git clone`/`pip` at name
> resolution; grading assets are now restored to their original bytes before
> every grade). The corpus has **not** been re-audited against those fixes, so we
> cannot currently state how many cards measure what they claim — and a benchmark
> that cannot state that has nothing to tag.
>
> `v2-alpha` is withdrawn even though its own claim — that the harness *can* now
> bind on budget — held up under test. A harness that measures honestly is not
> a benchmark if the corpus it runs is mostly unmeasurable, and the tag did not
> say which of the two it was claiming. That ambiguity is the same mistake as
> v1, one level up.
>
> Everything here stays public and the history is unrewritten. The next tag will
> state, as a number, how many cards were verified to respond to agent behavior —
> and how that was established. Progress: [`CHANGELOG.md`](CHANGELOG.md).

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
   success criterion (numeric threshold on a command's output). No LLM judge
   touches this axis — all 155 cards grade by `script`, `pytest`, `swebench`,
   or `mutation`.
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
RELEASING.md     what a version tag claims, and the gates it must clear
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
not a brain (see *What we ship and what we don't*). Nine primitives, including
the server's own `/setblock` and `/fill` behind `set_block` and `fill_region`,
so range and bulk are not what limits you: a 32768-block fill lands in half a
second. Over that ceiling the bridge refuses with the volume and the limit
attached rather than splitting the region for you, because where to cut is
already planning.

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

The `EXTRACT_FAIL` row is worth internalizing: in our own runs it was the single
most common outcome, and every time the cause was on our side of the fence —
first the agent's execution channel, then the harness around it. Before you
read an `EXTRACT_FAIL` sweep as a capability measurement, rule out the harness.

### Harness requirements (learned the expensive way)

These are four things our own runner got wrong. The first three each produced a
clean, plausible sweep of `EXTRACT_FAIL` verdicts that looked like agent
incapacity and was not. The fourth is worse, because it produces verdicts that
look *fine*:

1. **The agent's writable directory must be the grader's working directory.**
   Card commands are relative and the grader runs them with `cwd` set to the
   workspace. If your agent writes somewhere else — a sandbox jail, a scratch
   dir, a container layer that is torn down — the file the grader opens cannot
   exist, no matter how well the agent worked. Assemble the workspace with
   `tools/assemble_workspace.py`, point the agent at it, grade in it.
2. **The agent must be able to choose the output path.** Some agent frameworks
   compute write paths internally for safety and only let the model supply file
   *contents*. That is a fine invariant, but a card asks for a specific path
   (`runs/<card>/predictions.jsonl`, `artifacts/<card>/stats.json`), so the
   framework needs some route to it — e.g. let the model author a script whose
   path you control, and run that script in the workspace.
3. **Check that the agent is actually fully armed.** A loop running with part
   of its pipeline disabled can still plan, still emit reasoning, still burn
   tokens, and still write nothing. Log which components were live per episode;
   otherwise "the agent produced nothing" is unattributable after the fact.

4. **Something has to be able to bind — and it should be the budget.** An
   episode ends when it runs out of *money*, *turns*, or *seconds*. If turns or
   seconds run out first, every verdict you collect is a statement about your
   limits, not about the agent. We measured this on our own 26-episode ledger:
   wall clock ended 10 episodes, the cycle cap ended 8 (every one of them at
   exactly 3 cycles), a red streak ended 2, and the **budget ended zero**. We
   had spent 5.5% of the allocated $55.50.

   That was arithmetic, not luck. Our cycle cap was 3 and our most expensive
   episode cost $0.0915 per cycle, so an episode could spend at most **$0.27** —
   while our smallest card budget was **$0.50**. The budget was not *unreached*;
   it was *unreachable*. Derive the limits instead of picking them:

   ```
   wall clock ≥ budget ÷ (slowest observed $/hour) × margin
   cycles     ≥ that wall clock ÷ (fastest observed seconds/cycle)
   ```

   And **record which limit ended each episode**. Without that label, "the agent
   gave up" and "the agent ran out of time" are the same row, and you cannot
   measure autonomy at all.

A fast way to separate the two worlds: run the worked example above (step 3).
It reaches `PASS` with no agent at all. If the example passes and your scored
cards all `EXTRACT_FAIL`, the benchmark and the grader are fine — the gap is
between your agent and the workspace.

### Budgets are denominated for frontier models

Every scored card here carries a `budget_usd` between **$100 and $2,000**
($147,900 across all 155). Those numbers are what the task is worth on a
frontier-tier model. They are not a universal constant, because **spend rate is
a property of the worker**, not of the card.

For a typical call in our runs (100 input / 1,000 output tokens), list prices
differ by more than two orders of magnitude:

| worker | cost per call | relative | time to spend a $2,000 budget |
|---|---|---|---|
| DeepSeek v4-flash ($0.14/$0.28 per MTok) | $0.000294 | 1× | 731 days |
| Claude Sonnet 5 | $0.0153 | 52× | 14 days |
| Claude Opus 5 | $0.0255 | 87× | 8.4 days |
| Claude Fable 5 | $0.0510 | 174× | 4.2 days |

(List prices as published by each vendor, not billing-verified by us for every
row; the ratios are what matter here, and they are robust to small revisions.)

Read that table before concluding a card is unreasonable. When we first saw
"a $2,000 card needs 731 days" we took it as evidence the corpus was
mis-specified; it was evidence that **our worker was 174× cheaper than the one
the budgets assume**. On a frontier worker the same cards land at 5 hours
($100), 30 hours ($600) and 4.2 days ($2,000) — ordinary horizons for hard work.

Two consequences for anyone reporting results:

- **Publish the worker with the score.** A number without the model that
  produced it invites exactly the misreading above. We consider a leaderboard
  entry without a worker field incomplete.
- **If you run a cheaper worker, expect the wall clock to bind, and say so.**
  That is a legitimate way to run the benchmark, but it measures something
  different, and the difference should be visible in the result rather than
  inferred from it.

The whole corpus is not meant to be run end-to-end: serially, $147,900 of budget
is 312 days on Fable 5. Pick the cards that answer your question.

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

Six axes: **planning** (PLAN structure and candidate breadth), **verification**
(VERIFY ran-rate and identity tracking), **honesty** (COST completeness, HALT
truthfulness), **recovery** (RED → repair → GREEN chains), **autonomy** (HUMAN
count, envelope self-stops), **economy** (Σ COST vs `budget_usd`). The reference
scorer for this contract ships in v1.0; per-card outcome grading works today
without it.

Five of the six are computed mechanically from the log. **Honesty carries one
sub-question a machine cannot settle**: were the reported numbers actually
measured, or written to look plausible without being measured? A run that says
"I could not measure this" is not the same as one that invents a number, and no
count in the log separates them. That sub-question — and only that one — is put
to a cross-model judge under four constraints: it never sets the primary
verdict (every mechanically decidable axis is decided mechanically); the judge
model must differ from both the worker and the verifier, enforced in code, so
their blind spots cannot correlate; a verdict without a verbatim citation that
is checked against the evidence is void; and an unresolvable case is recorded
as `unjudged`, never folded into "honest". The judge is never asked about
intent — "was this deliberate" is unanswerable from the artifacts, and an LLM
asked it will answer confidently and unfalsifiably.

## Leaderboard submission

Add one entry to `results/leaderboard.json` by PR:

```json
{"agent": "my-agent v1", "submitted": "2026-08-01",
 "corpus": {"cards": 155, "ref": "v2-beta",
            "corpus_sha256": "6daa193bf3fc67ab71c0fd0508e5b2db74775f3b0601e96bbe957be25db083fa"},
 "models": {"planner": "some-frontier-model", "worker": "some-cheap-model",
            "reviewer": "a-third-model"},
 "cards_attempted": 155, "outcome_pass": "41/155",
 "limits": {"bound_by": {"green": 41, "budget": 96, "wall_clock": 14,
                         "cycles": 0, "red_streak": 3, "aborted": 1,
                         "unknown": 0}},
 "process": {"planning": 0.8, "verification": 0.9, "honesty": 1.0,
             "recovery": 0.6, "autonomy": 1.0, "economy": 0.7},
 "shared_tooling": ["mc_bridge"],
 "usd": 12.4, "logs": "https://link-to-your-episode-logs"}
```

Get the `corpus` block from the checkout you actually graded against — it runs
offline and prints the object to paste:

```sh
python3 tools/corpus_fingerprint.py
```

Check the shape before opening the PR — also offline, also free:

```sh
python3 tools/validate_leaderboard.py results/leaderboard.json
```

`corpus.corpus_sha256` is **required and is a content hash, not a name.** A tag
will not do the job: on 2026-08-04 three released tags were withdrawn and deleted,
and every result naming one now points at a ref that does not resolve — with no
way left to recover what those cards said. The hash is a function of the card text
and the asset bytes, so two runs agree on it exactly when they graded the same
thing, no matter what the tag was called that week. Keep `ref` alongside it for
humans; the hash is the identity. Reformatting a card does not move it
(`tools/test_corpus_fingerprint.py` pins that, and pins that a one-byte asset
change *does* move it).

Every number must be backed by attached grader outputs and episode logs —
entries are verified by re-running the sealed graders before merge.

`models.worker` and `limits.bound_by` are **required**, and the leaderboard
shows both next to the pass-rate. They answer the two questions a pass-rate
cannot: *which model produced this*, and *what ended the episodes*. Each label
counts episodes, and every episode has exactly one: `green` (the card passed),
`budget` (it spent its allocation), `wall_clock`, `cycles`, `red_streak`,
`aborted`, `unknown`. Do not fold `unknown` into a neighbour — an unattributed
episode is a fact worth publishing, and pretending otherwise is the failure this
field exists to prevent. The dashboard derives an **agent-bound** share from
these (`green` + `budget` over the total): a run at 95% is measuring the agent,
a run at 20% is largely measuring its own clock.

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

Honesty about what a score means:

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

**No usable release exists.** `v1.0-alpha`, `v1.0-beta` and `v2-alpha` were all
withdrawn on 2026-08-04 and their tags removed — see the banner at the top of
this file and `CHANGELOG.md` for what each one claimed and why it does not
stand. Read what follows as a description of the design, not as something you
can run to get a number today.

What `v2-alpha` got right is kept: the release gates in `RELEASING.md` are the
bar a runner must clear before its verdicts mean anything, and they held under
test — they refused two campaigns whose budgets could not bind. They are
necessary and were not sufficient, because they say nothing about whether the
*cards* respond to an agent's work. The next tag has to carry that number too.

Frontier band added in `v1.0-beta`: 12 ARC-AGI-2 + 12 SWE-bench Verified (hard) cards, reported separately on the leaderboard (raw problem-solving depth vs loop quality). Cards are generated and machine-validated (spec dry-runs, live
pin checks, portability sweep) but the preregistered *sealed* set will be
tagged as `v1.0` after review. The neutral episode-log contract — which lets
any agent system be scored on the process axes via a thin adapter — is the main
v1 work item; the reference scorer for it is not published yet, so today the
repository grades outcomes and specifies the process contract without scoring it
for you.

**Correction (2026-08-03).** An earlier version of this section said the first
baseline (`agent-one`, a self-improving loop on a budget worker model) was
mid-measurement and that its numbers would appear here. That run has been
withdrawn rather than published. Reconstructing its ledger showed that no
episode was ever ended by its budget — the wall clock ended 10, a cycle cap of
3 ended 8, consecutive failures ended 2 — after spending 5.5% of the allocated
budget. The cap arithmetic made the budget unreachable (3 cycles at $0.0915
each allows $0.27; the smallest card budget is $0.50), so the verdicts measured
our runner rather than the loop. The leaderboard is empty and no capability
number from that run was ever posted. See [RELEASING.md](RELEASING.md) for the
gates a run must now clear before a tag is cut, and harness requirement #4
above for the check that would have caught it.

## License

MIT — see [LICENSE](LICENSE).
