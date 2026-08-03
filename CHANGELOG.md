# Changelog

## Unreleased

### Correction — "No LLM judges" was a claim about one axis, printed as a claim about the benchmark

`v2-alpha` shipped with `No LLM judges` in the README's opening summary and as a
`0 LLM judges` badge on the dashboard. On the outcome axis that is exactly true
and stays true: all 155 cards grade by `script` (80), `pytest` (36), `swebench`
(23), or `mutation` (16), and none of those consults a model.

It was never true of the whole benchmark, because the process axis was always
going to need one thing a machine cannot settle: whether a reported number was
**measured** or written to look plausible without being measured. A run that
says "I could not measure this" and a run that invents a figure produce logs
that no count distinguishes. That sub-question — one of six process axes, and
only that one — goes to a cross-model judge, under four constraints: it never
sets the primary verdict; the judge model must differ from both worker and
verifier, enforced in code, so their blind spots cannot correlate; a verdict
without a verbatim citation checked against the evidence is void; and an
unresolvable case is recorded as `unjudged` rather than folded into "honest".
The judge is not asked about intent — that is not answerable from the artifacts.

The badge now reads `0 judges on outcome`, which is what we can defend, and the
scope of the judge is stated where the process axis is described rather than
being absent from the summary.

Neither number in any published run changes: the judge has no runtime caller
today, so nothing that has been graded was graded with one.

## v2-alpha — 2026-08-03

A harness release. **The card set is unchanged from `v1.0-beta`** — we measured
all 236 internal cards for mechanical defects and found none. What was broken
was the harness around them, so that is what this tag changes.

### The correction that made this necessary

`v1.0-beta` was tagged without stating what a tag claims. Reconstructing our own
26-episode ledger showed that no episode had ever ended by exhausting its
budget: 10 ended on the wall clock, 8 on the cycle cap (every one at exactly 3
cycles), 2 on consecutive failures, 0 on budget. We had spent 5.5% of what we
allocated.

That was arithmetic, not bad luck. A cycle cap of 3, at our most expensive
$0.0915 per cycle, permits $0.27 — and the smallest card budget in the set is
$0.50. The budget was not unreached, it was **unreachable**. Every verdict we
had was a statement about our runner's limits rather than about any agent.

Nothing in the tag, the cards, the tools, or the leaderboard would have told a
reader that.

### What changed

- **`RELEASING.md`** — states what a version tag claims and the gates that have
  to hold before one is cut (G1 budget can bind, G1b the campaign can afford the
  cards, G2 every entry names its worker and its binding limit, G3 the
  agent-bound share is reported, G4 no trap card is public, G5 every number
  traces to a ledger row). Each gate is a command rather than a judgement.
- **`tools/validate_leaderboard.py`** (new) — enforces `models.worker` and
  `limits.bound_by`. Spend rate is a property of the worker: list prices span
  more than 100× between tiers, so the same `budget_usd` is a different amount
  of work depending on who is doing it.
- **`tools/build_dashboard.py`** — shows the worker and the agent-bound share
  per entry.
- **`README.md`** — harness requirement #4 (the budget must be able to bind),
  and an explicit statement that card budgets are denominated for frontier
  models. A worker two orders of magnitude cheaper will be clock-bound at these
  budgets no matter how patient the operator is. That is a legitimate way to use
  the benchmark; it just measures something narrower, and the entry has to say
  so.
- **Baseline withdrawn** — the `agent-one` leaderboard entry was removed. It
  could not have measured what it claimed, and leaving it up while publishing
  the gate that invalidates it would be the same defect one level higher.

### What this tag does not claim

- **Not** that we have measured any agent under these gates. At the moment this
  tag was cut our own reference configuration **failed G1**: at 1.5 h and 3
  cycles per episode it would have needed 26.3 h and 386 cycles for the budget
  to bind. That was stated here rather than fixed quietly, because a runner that
  fails G1 is exactly the condition this release exists to make visible.

  *Update, same day:* the reference configuration was brought into compliance
  (26.3 h wall clock, 386 cycles, a consecutive-failure cap of 97, and a
  campaign ceiling raised to cover the sum of the card budgets) and a
  budget-bound run is in progress. No results from it are published here yet,
  and none will be until every gate above holds for the run that produced them.
- **Not** that the card set is complete, balanced, or contamination-free.
- **Not** that a high score generalizes. These are 155 specific tasks.
- **Not** that the process axes are validated as constructs. They are a coverage
  checklist, and treating them as design targets is a known way to produce a
  benchmark that measures its own vocabulary.

### Gate status at tag time

| gate | scope | status |
|---|---|---|
| G1 — budget can bind | the runner | **not met by our reference config** (stated above) |
| G1b — campaign affords the cards | the runner | **not met by our reference config** |
| G2 — worker + binding limit required | this repo | met (`validate_leaderboard.py`, exit 0) |
| G3 — agent-bound share reported | this repo | met (dashboard column) |
| G4 — no trap card in `cards/` | this repo | met (155 cards, 0 traps) |
| G5 — every number traces to a ledger row | this repo | met (0 entries; the one that could not was withdrawn) |

## v1.0-beta

Initial public card set and tooling. See `RELEASING.md` for why its claims were
narrower than they appeared.
