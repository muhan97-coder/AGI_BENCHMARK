# cronnext — cron schedule computation library (spec v1)

Implement a pure-Python module at `workspace/gc-400/cronnext.py` (relative to
the benchmark repo root). Standard library only. All times are UTC; there is
no DST anywhere in this spec.

## Expression format (5 fields, whitespace separated)
    minute hour day-of-month month day-of-week
- minute: 0-59, hour: 0-23, day-of-month: 1-31, month: 1-12,
  day-of-week: 0-7 (BOTH 0 and 7 mean Sunday).
- Each field is a comma-separated list of items. An item is one of:
  - `*` — all values
  - `*/S` — all values stepping by S from the field minimum
    (`*/10` in day-of-month = days 1, 11, 21, 31 — steps anchor at the MIN)
  - `N` — single value
  - `N-M` — inclusive range; requires `N <= M` using the raw numeric values
    (no wraparound; `5-1` is invalid). For day-of-week, `5-7` is legal and
    means {5, 6, 7} with 7 normalized to Sunday AFTER expansion, i.e.
    {Fri, Sat, Sun}.
  - `N-M/S` — range with step S (from N).
- Steps must be integers >= 1. `*/1` is legal.
- Month names JAN..DEC and day names SUN..SAT are accepted case-insensitively
  wherever a numeric value is accepted in that field (including in ranges:
  `MON-FRI`). SUN maps to 0.
- Anything else (wrong field count, out-of-range values, empty items, step 0,
  reversed ranges, unknown names) is invalid.

## Day matching (Vixie rule — deliberately tricky)
A field counts as **restricted** unless its full text is exactly `*`
(`*/2` IS restricted). Day-of-month and day-of-week combine as follows:
- both restricted: the day matches if EITHER field matches (OR)
- otherwise: the day matches if BOTH match (the unrestricted one always does)

Example: `0 0 13 * 5` fires on the 13th of every month AND on every Friday.
`0 0 13 * *` fires only on the 13th.

## API
### `is_valid(expr: str) -> bool`
### `next_fires(expr: str, start: str, n: int) -> list[str]`
- `start` is `YYYY-MM-DDTHH:MM` with an optional trailing `Z`.
- Returns the first `n` fire times STRICTLY AFTER `start` (a fire time equal
  to `start` is excluded), formatted `YYYY-MM-DDTHH:MM`, ascending.
- Search horizon: `start` + 1826 days. If fewer than `n` fire times exist in
  the horizon (e.g. `0 0 31 4 *` — April has 30 days), raise `ValueError`.
- Invalid expression or malformed `start`: raise `ValueError`.
- `n` must be an integer >= 1, else `ValueError`.

## More deliberately tricky cases (all tested)
- `0 0 29 2 *` fires only on leap-year Feb 29.
- `0 0 31 * *` silently skips 30-day months and February.
- Names are case-insensitive: `0 12 * mAr Mon-fri` is valid.
- `7` and `0` in day-of-week are the same day: `0 0 * * 7` == `0 0 * * 0`.
- Minute/hour steps anchor at 0: `*/15` in minutes = 0, 15, 30, 45.
- Strictly-after: with expr `* * * * *` and start `2030-01-01T00:00`, the
  first fire is `2030-01-01T00:01`.

## Acceptance
Sealed suite: `assets/gc-400/test_accept.py`, run from the repo root with
pytest. Do not modify the test file.
