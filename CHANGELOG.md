# Changelog

## 2026-08-04 — infra_ops cards were unpassable; the harness erased the deliverable

The 12 `infra_ops` cards each name, in prose, the file the agent is supposed to
edit:

> Only `tuned/postgresql.conf` may be edited; the baseline config and
> `check.sh` are sealed.  — gc-373

None of the 12 said so in the schema. `assets_visibility` was empty on all of
them, and the runner restores every asset to its pristine bytes before grading
(that rule exists to stop an agent patching the grader, and it is the right
rule). Run end to end on gc-372: the agent's repairs — `nginx:latest` →
`nginx:1.25.4`, `redis:7.2.4-bogus` → `redis:7.2.4`, host port `8080` → `8372` —
were all reverted, **and the repairs were recorded as `tampered`.** Doing the
assigned work scored as cheating, and the card could not be passed no matter how
capable the agent was.

This is not a contradiction between the two rules. Both are right; the card had
no way to say which files it meant. That is the same shape as `resources` and
`process_expectations`, which the cards also filled in and no code read.

### Fixed

`assets_visibility.editable` — a list of paths or globs, relative to
`assets/<card-id>/`. A directory entry covers everything under it. The runner
keeps those files as the agent left them and restores everything else,
so `check.sh`, baselines and sealed inputs stay protected. All 12 cards now
declare what their own prose already said; nothing else about the cards changed.

**Editable does not mean unchecked.** A file that is not restored can be handed
over as a symlink, and the sealed `check.sh` mounts it with `docker run -v` —
docker follows the link (measured: the link target `/etc` appeared whole inside
the container). So the contract is "your content, but a regular file": a symlink
or a directory in an editable slot is removed, the original is put back, and the
substitution is recorded.

`corpus_sha256` is now
`224fa198dd1c84719d8842fddfe999e6378ff5d0f366c9d4a4501895eefaf5b2`.

### Also

The leaderboard template in README.md carried a concrete-looking
`corpus_sha256`. Copying it verbatim would have attached a hash that does not
match the corpus actually run — the exact failure the field exists to prevent.
It is now a placeholder, and the validator rejects it (as it already rejected a
tag name in that slot).

## 2026-08-04 — all released versions withdrawn

`v1.0-alpha`, `v1.0-beta` and `v2-alpha` are withdrawn; their tags are removed
from the repository. Nothing is deleted or rewritten — the commits they pointed
at remain in history, and this file records what they claimed and why the claims
do not stand.

### Why the v1 tags go

They never measured an agent. Across 26 episodes not one ended by exhausting its
budget — 10 hit the wall clock, 8 the cycle cap (all at exactly 3 cycles), 2 the
consecutive-failure cap, 0 the budget. With a cycle cap of 3 and a worst-case
$0.0915 per cycle, the reachable spend was $0.27 against a smallest card budget
of $0.50: the budget was **unreachable**, not merely unreached. Every verdict was
a fact about our runner.

### Why `v2-alpha` goes too

Its own claim survived testing. The budget-binding gates work: on 2026-08-03 they
refused to launch two campaigns whose budgets could not bind, and an armed run
held a stable spend rate for six hours, with the budget on track to bind before
the wall clock. That part is real.

It is withdrawn because **a harness that measures honestly is not a benchmark if
the corpus is mostly unmeasurable**, and the tag never said which of the two it
was claiming. A read-only audit of all 155 cards (2026-08-02) found 90 that
cannot move their own metric except by forgery, 24 that measure test-rewriting
rather than the stated task, 20 unverified one-shots, and 21 that respond
honestly to sandbox behavior.

Part of that was ours and is fixed: `/etc/resolv.conf` was a symlink into a path
the sandbox did not mount, so DNS died inside the jail while raw TCP stayed up —
`git clone` and `pip` failed at name resolution, which the audit named as the
single largest cause. Grading assets are now restored to their original bytes
before every grade, whether or not they were sealed, with tampering counted on
the ledger rather than silently reverted.

The corpus has not been re-audited since those fixes landed, so the 21 figure is
stale in an unknown direction and we will not quote it as current. That, on its
own, is why no tag can stand: we do not currently know how many cards measure
what they claim.

> **Correction (same day, before anyone could rely on it).** The first version of
> this entry also said that for 17 cards the expected-answer file is staged into
> the agent's workspace. That is wrong. Those cards declare the answer file under
> `assets_visibility.sealed`, and the workspace builder skips sealed names and
> `*.sha256` commitments when it stages assets — verified by running the builder
> against the private asset tree: 6 files present, 4 staged, `sealed_excluded: 2`,
> no `expected_*` in the agent's view. The error was reading "the answer file sits
> in the same directory" as "the agent can see it", without checking the mechanism
> that exists to prevent exactly that. The withdrawal stands on the two reasons
> above; this was not one of them.

### What a future tag has to carry

A count — how many cards were **verified** to respond to agent behavior — and the
method that established it. A version number that does not say what it measured
is how both of these releases went wrong.

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
