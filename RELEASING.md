# What a version tag means here

A tag on this repository is a claim about the **harness**, not about any agent.
It says: if you run the tagged card set with a runner that meets the gates
below, the verdicts you get describe the agent you pointed at it.

That claim is falsifiable, so the gates are written to be checked by someone
other than us — each one is a command, not a judgement.

## Why this file exists

`v1.0-beta` was tagged without a bar like this, and it turned out that our own
runs could not have measured what the tag implied. Reconstructing our
26-episode ledger on 2026-08-03:

| what ended the episode | count |
|---|---|
| wall clock | 10 |
| cycle cap | 8 (every one at exactly 3 cycles) |
| consecutive failures | 2 |
| **budget** | **0** |

We had spent 5.5% of the allocated budget. And that was arithmetic rather than
bad luck: a cycle cap of 3, at our most expensive $0.0915 per cycle, allows
$0.27 — while the smallest card budget in the set was $0.50. The budget was not
*unreached*, it was *unreachable*, so every verdict was a statement about our
runner's limits.

Nothing in the tag, the cards, or the leaderboard would have told a reader that.
The gates below exist so the next tag cannot be in that position quietly.

## Gates

> **`v2-alpha` was withdrawn on 2026-08-04** (with `v1.0-alpha` and `v1.0-beta`).
> These gates are not withdrawn — they held under test, refusing two campaigns
> whose budgets could not bind. They were **necessary and not sufficient**: every
> one of them is about the runner, and none of them asks whether the cards
> themselves respond to an agent's work. A corpus audit found most do not. The
> next tag needs a gate for that, stated as a verified count.

### G0 — the grading authority must match the executable surface

```sh
python3 tools/grading_surface.py check --require-explicit
python3 -m unittest tools.test_grading_surface
```

The first command fixes the denominator before any other claim is made: 167
scored cards, 120 whose commands invoke a local evaluator, including the 96
`grade.py`/`check.sh` cards and the 24 `test_accept.py` cards. The descriptive
`grader` field is not the filter. Each of those 120 cards must declare the exact
same authority under `assets_visibility.grader_sealed`.

`grader_sealed` is public candidate-visible code whose trusted bytes are
restored immediately before authoritative grading and verified afterward. It
must not overlap `editable` or hidden-answer `sealed`. The test command proves
that candidate stubs and symlink/hardlink/FIFO substitutions fail closed. This
gate closes persistent function replacement; process/namespace isolation is a
separate stronger gate for same-user replacement races.

### G1 — the budget must be able to bind

For every card in the tagged set, with the runner configuration and worker you
intend to use:

```
wall clock ≥ budget_usd ÷ (slowest observed $/hour for that worker) × margin
cycles     ≥ that wall clock ÷ (fastest observed seconds/cycle)
red streak ≥ some fraction of that cycle count
```

`budget_usd` here is **the cap your runner actually hands the agent**, not the
number printed on the card. If your harness clamps per-card budgets, the clamp
is the budget — checking the card's figure computes a requirement for money that
will never be spendable. We got this wrong in our own checker: 50 of our 79
cards were clamped, and for one of them the check demanded a 236-hour wall clock
where 26 hours was enough.

The third line matters because raising only the cycle cap moves the binding
constraint rather than removing it — in our runs the cycle cap and the
consecutive-failure cap were degenerate, so lifting one just handed the episode
to the other.

If any bound is smaller, the episode ends on the clock or a counter before the
agent can spend what it was given, and the run measures the runner. Check this
**before** the run, not after: it costs nothing and it is the one failure that
produces results which look entirely normal.

A run that deliberately caps time below this is fine — see G3. What is not fine
is doing it without knowing.

### G1b — the campaign budget must cover the cards

Once per-episode budgets can bind, each card can actually spend its allocation,
and the next constraint is whatever ceiling covers the whole run. If that
ceiling is below the sum of the per-card budgets, the later cards do not run at
all — and a card that did not run is **not a failure**, it is an absence of
measurement. Report the two numbers side by side; do not fold this into G1,
because "the episode could spend its budget" and "the campaign could afford the
episode" fail in different ways and want different fixes.

### G2 — every entry names its worker and what ended its episodes

```sh
python3 tools/validate_leaderboard.py results/leaderboard.json   # exit 0
```

`models.worker` is required because spend rate is a property of the worker: for
a typical call in our runs, list prices span more than 100× between tiers, so
the same `budget_usd` is a different amount of work depending on who is doing
it. `limits.bound_by` is required for the reason above.

### G3 — the agent-bound share is reported, not required to be high

Each entry reports how many episodes ended by `green` or `budget` versus by the
runner's clock or turn cap. The leaderboard derives the share and shows it.

We considered requiring a high share and decided against it. Running a cheaper
worker against budgets denominated for frontier models will be clock-bound no
matter how patient you are, and that is a legitimate way to use this benchmark —
it just measures something narrower. The defect was never the clock-bound run;
it was the clock-bound run that did not say so.

### G4 — no trap card is in the public corpus

Some cards in our internal set are **traps**: a cheap shortcut is deliberately
left open, the grader does not block it, and a detector outside the agent's
sandbox records whether it was taken. Publishing one destroys it — a shortcut
you have read about is no longer a measurement of what you do when you think
nobody is looking.

Traps therefore never appear in `cards/`, and a tag is not cut until that is
verified. This is stated publicly rather than hidden because the *existence* of
traps is not the secret; which cards and which shortcuts are.

### G5 — every published number traces to a ledger row

Entries are verified by re-running the sealed graders before merge. A number
that cannot be pointed at a specific episode's grader output does not go on the
board.

## What a tag does not mean

- **Not** that the card set is complete, balanced, or contamination-free.
- **Not** that a high score generalizes. These are 167 specific tasks.
- **Not** that the process axes are validated as constructs. They are a
  coverage checklist, and treating them as design targets is a known way to
  produce a benchmark that measures its own vocabulary.
- **Not** an endorsement of any worker. The price table in the README is there
  so runs can be compared, not ranked by cost.
