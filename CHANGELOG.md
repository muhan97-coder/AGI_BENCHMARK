# Changelog

## 2026-08-25 — one grader-authority predicate and trusted restoration

The public corpus had three incompatible denominators for the same security
question: 92 cards labelled `grader: script`, 96 commands naming `grade.py` or
`check.sh`, and 120 commands that actually execute candidate-writable local
evaluator code. The last number is the authority boundary: it also includes 24
`test_accept.py` cards. The corpus now has one machine-checkable predicate and a
fixed census of **167 total / 120 local evaluator / 96 grade-or-check / 12
Minecraft self-report**. The self-report cards remain a separate grader-redesign
cohort rather than being miscounted as sealed local code.

### Fixed

- `tools/grading_surface.py` defines the command-derived population, checks the
  fixed census, synchronizes explicit manifests only with `sync --apply`, and
  safely reads/restores bounded regular single-link evaluator files.
- All 120 affected cards now declare their exact evaluator authority under
  `assets_visibility.grader_sealed`. This is public candidate-visible code, not
  the hidden answer-pack meaning of `assets_visibility.sealed`; the two fields
  cannot overlap, and neither can overlap `editable`.
- `assemble_workspace.py` applies the predicate even if a manifest is absent,
  includes evaluator code read-only for candidate iteration, and refuses stale
  destinations or link/special-file source trees.
- `goal_grader.py` atomically restores evaluator bytes from the trusted checkout
  immediately before execution and verifies hash, type, link count, and
  read-only mode afterward. Candidate stubs and symlink/hardlink/FIFO
  substitutions fail closed as `GRADER_INVALID` or `GRADER_TAMPERED`.

No goal, threshold, budget, answer, or success criterion changed, so this is a
measurement-integrity repair rather than task fitting. It closes persistent
grader-function replacement. It does **not** claim to close an adversarial
same-UID race between restore and execution; that requires a separate isolated
grading process/read-only mount. The 12 Minecraft self-report graders likewise
remain outside this file-sealing repair.

## 2026-08-22 — frontier_arc3: ARC-AGI-3 replaces ARC-AGI-2 as the live frontier band

`frontier_arc` (ARC-AGI-2, gc-440..gc-451, 12 cards) is a static grid-puzzle
corpus with public gold. Saturation evidence: 2026-08-21 public leaderboards
put top ARC-AGI-2 scores at ~92.5% (GPT-5.6 Sol) / ~90.4% (Opus 5) — frontier
worker models one-shot most of the corpus, so the band measures the model, not
the loop. Separately, NVIDIA's AVO result (2026-08-21, on ARC-AGI-*3*: the
same model swinging ~30%→100% purely from scaffolding) is why the replacement
band is the right target — ARC-AGI-3 discriminates harnesses, which is exactly
what this repository scores. (Correction 2026-08-22: an earlier draft of this
entry cited the AVO number as if it were ARC-AGI-2 saturation evidence — wrong
benchmark; caught by adversarial review.) `frontier_arc` is marked **saturated** and
kept for history: existing cards are not removed or re-scored, they are just
no longer where new frontier signal is sought.

**Known integrity gap (adversarially demonstrated 2026-08-22, repo-wide, not
arc3-specific):** `tools/goal_grader.py` executes the grade command inside
whatever workspace it is pointed at. If that is the *agent's* workspace, the
agent can overwrite its copy of `assets/<id>/grade.py` (or widen
`game_ids.txt`) and forge a PASS — demonstrated live against gc-464. The
operating contract is therefore: **grade in a fresh, maintainer-side
workspace** re-assembled from this repo's canonical assets, copying only the
agent's `runs/` output in. A structural fix (goal_grader verifying asset
bytes against the repo before running, or refusing workspaces whose assets
differ) is TODO. A second structural gap: `grade.py` verifies the scorecard
via live server GET but does not (cannot, today) bind it to *this* run's
session/owner — a stale or foreign scorecard id on an allowed game would
pass; mitigated only by the honest-ledger process expectations until the API
exposes an ownership field.

> **Resolution 2026-08-25:** persistent replacement of the local grader
> function is closed by the command-derived 120-card authority manifest plus
> trusted pre-run restoration and post-run verification described above. The
> stronger same-UID race and the live scorecard ownership/session binding remain
> open and are not represented as solved.

### Added

- **`frontier_arc3`** (gc-464..gc-475, 12 cards) — ARC-AGI-3
  (docs.arcprize.org, launched 2026-03-25), an interactive game environment.
  An agent drives a live session against `https://three.arcprize.org` through
  `POST /api/scorecard/open` → `RESET`/`ACTION1..7` → `POST
  /api/scorecard/close`, and the grader (`assets/gc-4NN/grade.py`, stdlib-only)
  reads the result back with a live `GET /api/scorecard/{id}` rather than
  checking any local prediction file. There is no public gold to leak because
  there is no static answer, only a play session the server itself recorded —
  the new closed-vocabulary value **`contamination_risk: no_public_gold`**
  names this directly (12 cards).
- Ladder: smoke (gc-464/465, 1 level of 1 game) → single-game level
  progression (gc-466..468, 3 levels each) → breadth across all 3 games
  (gc-469/470) → RHAE-efficiency and transfer (gc-471..473, scored against the
  server's own `score` field per docs.arcprize.org/methodology) → capstone
  (gc-474/475, depth **and** efficiency together). Budget/horizon tiers reuse
  the existing `1d`≤$100 / `1w`≤$600 / `1m`≤$2000 ceilings; the 1w/1m tiers
  carry the interactive-step cost explicitly in their resources text (every
  RESET/ACTION is a real turn against a live, rate-limited session, not a
  free static grid to stare at).
- **Scoped to 3 games, not 5.** Investigation (2026-08-22) confirmed exactly
  three public game ids against official ARC Prize documentation — `ls20`,
  `ft09`, `vc33` — cross-checked against `docs.arcprize.org/available-games`
  and the `/api/games` response example embedded in the OpenAPI spec. A
  longer ~25-game roster is reported by the official benchmarking harness and
  circulates in an unofficial community mirror repo, but neither is an
  ARC-Prize-published id list, so no card here seals against it. The
  `assets/gc-4NN/game_ids.txt` allowlists therefore draw only from the
  confirmed three; `examples/frontier_arc3/README.md` carries the full
  provenance note and citations.
- `examples/frontier_arc3/README.md` — setup (`ARC_API_KEY` registration,
  `pip install arc-agi==0.9.9`) and an agent-loop skeleton. Unlike the other
  twelve `examples/<category>/` demos this is documentation only, not an
  offline `card.json` + `solution/` teaching demo: `frontier_arc3` grading is
  a live network call against a real account, which an offline demo cannot
  honestly reproduce.

`corpus_sha256` after this change is printed by `tools/corpus_fingerprint.py`;
paste its live output into a leaderboard entry rather than copying a number
out of this file, since the whole point of the corpus hash is that it is
recomputed, not quoted.

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
and stays true: all 167 cards grade by `script` (92), `pytest` (36), `swebench`
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
