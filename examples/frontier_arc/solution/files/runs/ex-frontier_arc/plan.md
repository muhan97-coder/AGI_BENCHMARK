# ex-frontier_arc — plan (written before the first prediction)

Verification command (the only thing that decides): `python3 assets/ex-frontier_arc/grade.py`
Threshold: `solved >= 2` of 3. Attempt budget: 2 attempts per test input, spent on
*distinct* rules — a second attempt that is a typo-fix of the first buys nothing.

## Order of attack

Cheapest-hypothesis-first, so a failure teaches something before the budget is spent.

| # | task | first read of the train pairs | risk |
|---|---|---|---|
| 1 | `ex03_recolor` | shape is preserved, only colours change → look for a per-colour map | low: 3 train pairs pin the map |
| 2 | `ex02_mirror` | output is twice as wide → concatenation with a reflection | medium: which side is mirrored, and around which axis |
| 3 | `ex01_fall` | shape preserved, non-zero cells end up at the bottom → column gravity | medium: does column order survive? |

## Hypotheses (each checked against EVERY train pair before any test prediction)

- **ex03_recolor** — `1→2, 2→3, 3→1`, `0` fixed. Checked on all 3 train pairs, all cells
  agree. Attempt 2 spends the budget on the *inverse* permutation (`1→3, 3→2, 2→1`),
  the only other cyclic map consistent with a "colours rotate" reading — a genuinely
  different rule, not a re-roll of the same one.
- **ex02_mirror** — `output[r] = input[r] + reverse(input[r])`: the grid is concatenated
  with its own left-right mirror, so width doubles and height is unchanged. Rejected on
  the way: "mirror on the left" (`reverse(row) + row`), which contradicts train pair 1
  (its first column would then read 0,0,3 instead of 1,0,0). Attempt 2 keeps the rejected
  variant, since it is the only other placement consistent with the doubled width.
  **This task has TWO test inputs — both must be right or the task scores zero.**
- **ex01_fall** — every non-zero cell falls to the bottom of its own column, preserving
  the top-to-bottom order of the cells within that column; empty cells become 0. Train
  pair 2 is the discriminator: its column 0 holds two 4s, and they stay adjacent at the
  bottom, which rules out "collapse to a single cell" and "sort the column".

## Checkpoints

1. Write `predictions.json` for all three tasks, run the grader (mid-run checkpoint),
   preserve the verdict line.
2. If `solved < 3`, re-read the train pairs of every not-solved task named on stderr,
   revise the hypothesis, re-run. Never look at `assets/ex-frontier_arc/gold/` — it is the
   grader's, and a prediction traced to it proves nothing.
3. Final run, preserve the verdict line, write `ledger.json`, HALT `goal_green`.
