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

## Gates for `v2-alpha`

### G1 — the budget must be able to bind

For every card in the tagged set, with the runner configuration and worker you
intend to use:

```
wall clock ≥ budget_usd ÷ (slowest observed $/hour for that worker) × margin
cycles     ≥ that wall clock ÷ (fastest observed seconds/cycle)
```

If either bound is smaller, the episode ends on the clock or the turn counter
before the agent can spend what it was given, and the run measures the runner.
Check this **before** the run, not after: it costs nothing and it is the one
failure that produces results which look entirely normal.

A run that deliberately caps time below this is fine — see G3. What is not fine
is doing it without knowing.

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
- **Not** that a high score generalizes. These are 155 specific tasks.
- **Not** that the process axes are validated as constructs. They are a
  coverage checklist, and treating them as design targets is a known way to
  produce a benchmark that measures its own vocabulary.
- **Not** an endorsement of any worker. The price table in the README is there
  so runs can be compared, not ranked by cost.
