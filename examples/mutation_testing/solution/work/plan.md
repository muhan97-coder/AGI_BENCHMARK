# Plan — ex-mutation_testing

Written before the first test, as the process expectation requires.

## 1. Behaviour inventory of `assets/target/tally.py`

| surface | observable behaviour | intended killer test |
|---|---|---|
| `normalize` | strips surrounding whitespace, then lowercases | assert on an input with leading/trailing spaces AND uppercase |
| `tally` | first occurrence counts as 1; keys are normalised | exact-dict assertion on repeats and on mixed-case/whitespace duplicates |
| `top_k` | descending frequency, ties alphabetical, truncated to k | three-tier frequency fixture + a tie fixture + a truncation assertion |
| `top_k` | `k == 0` returns `[]`; `k < 0` raises `ValueError` | boundary pair — the `k == 0` case is what pins the `<` vs `<=` guard |
| `share` | `0.0` on empty input; normalised lookup otherwise | empty-input assertion plus a mixed-case fraction assertion |

## 2. Loop discipline

1. Write the suite, run it against the pristine module — must be GREEN and
   collect at least 6 tests, otherwise nothing downstream means anything.
2. Run the sealed grader; read `killed_ids` from its JSON line.
3. For every survivor: decide **killable-next** (write the missing assertion,
   go to 1) or **suspected-equivalent** (argue it, and record it as a
   survivor — never as a kill).
4. Only then write `kill_report.json`, from the recomputed set, not from hope.

## 3. Expected survivors

`m05` rewrites `if not items:` as `if len(items) == 0:`. For a list argument
these are the same expression; no assertion can distinguish them. Verdict:
**suspected-equivalent**. It stays out of `killed` in the report, which is why
the achievable ceiling is 4/5 = 0.80 and the card threshold is 0.80, not 1.0.
