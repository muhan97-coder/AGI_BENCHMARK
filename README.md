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
cards/           131 goal cards (JSON) + cards/assets/<id>/ sealed assets
cards/INDEX.md   full card index with categories and difficulty
tools/goal_grader.py     the machine grader (stdlib only, fail-closed)
tools/build_dashboard.py rebuilds docs/index.html from cards/
docs/index.html  static dashboard (card browser + leaderboard)
results/leaderboard.json leaderboard entries (submit via PR)
```

## Quick start

```sh
# validate a card's grader spec (no execution, $0)
python3 tools/goal_grader.py --dry-run cards/gc-300_swebench_single_django.json

# have YOUR agent pursue the card's goal in a workspace, then grade it
python3 tools/goal_grader.py cards/gc-300_swebench_single_django.json cards
```

A card is a sealed contract: `goal` (what the agent must achieve), `budget_usd`
(spend envelope), `success_criteria.spec` (the grading command + numeric
threshold), and `process_expectations` (what observable good process looks
like). All resources are public and pinned (git SHAs, package versions, docker
tags); everything else ships in `cards/assets/`.

## Categories

SWE-bench (pinned Lite instances) · OSS repair at pinned SHAs · mutation
testing · Minecraft builds on fresh docker worlds · infra/ops tuning in docker ·
deterministic data reproduction · tool-from-spec with sealed acceptance tests ·
multi-stage campaigns · robustness/anti-gaming probes · MARBLE coding tasks.

## Contamination & leakage

Honesty about what a score means (v1.0-alpha):

- Every card carries `contamination_risk`:
  **`public_gold_exists`** (29 cards — SWE-bench gold patches are in the public
  dataset; OSS-repair fixes may exist in upstream history past the pinned SHA),
  **`answers_sealed`** (15 cards — the grader's answer files are **not in this
  repository**; only `<name>.sha256` commitments are. The sealed pack is held
  privately by the maintainers), **`low`** (87 cards — visible sealed
  tests/blueprints are the *spec*, not the answer; hard-coding-to-tests is
  countered by the mutation and robustness bands).
- **Oracle isolation** (v1.0-alpha, enforced):
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

**v1.0-alpha.** Cards are generated and machine-validated (spec dry-runs, live
pin checks, portability sweep) but the preregistered *sealed* set will be
tagged as `v1.0` after review. The neutral episode-log contract — which lets
any agent system be scored on the process axes via a thin adapter — is the main
v1 work item. First baseline (a self-improving agent loop on a budget worker
model) is being measured now.

## License

MIT — see [LICENSE](LICENSE).
