# gc-395 -- Reproduce sealed revenue rollups via a two-table ETL join

## Dataset

Two tables: assets/gc-395/orders.csv (order_id, customer_id, amount, order_day; 700 orders, some referencing unknown customers) and assets/gc-395/customers.csv (customer_id, segment, signup_day; 90 customers in segments consumer/business). Day columns are integer day indices on a shared axis.

File(s): `assets/gc-395/customers.csv`, `assets/gc-395/orders.csv`. Total size is under 100KB. The data is synthetic and
public-domain; regenerate it byte-identically (stdlib only, fixed seed) with:

    python3 assets/gc-395/make_dataset.py

run from the benchmark repo root. The sha256 of each data file is sealed in
`assets/gc-395/expected_stats.json` and is checked by the grader, so the
bundled data must not be modified.

## General conventions

- Parse numeric CSV fields as IEEE-754 doubles exactly as written.
- "sample" variance/std uses the n-1 denominator.
- quantile(q) uses linear interpolation between order statistics (Type 7, the
  numpy/pandas default): on the ascending sorted sample s (0-indexed) let
  h = (n-1)*q; the result is s[floor(h)] + (h-floor(h)) * (s[floor(h)+1] - s[floor(h)]).
- median = quantile(0.5).
- Count-valued statistics are submitted as numbers like every other statistic.
- Validity filtering: an order is valid if and only if its customer exists AND order_day >= that customer's signup_day. All 'valid' statistics use exactly this set.
- Amounts are parsed as decimals exactly as written in the CSV.

## The 12 sealed statistics

| # | name | definition |
|---|------|------------|
| 1 | `n_orders_raw` | rows in orders.csv |
| 2 | `n_orders_joined` | orders whose customer_id exists in customers.csv |
| 3 | `n_orders_valid` | joined orders with order_day >= signup_day (integers) |
| 4 | `revenue_total` | sum of amount over valid orders |
| 5 | `revenue_mean` | revenue_total / n_orders_valid |
| 6 | `revenue_consumer` | sum of amount over valid orders whose customer segment is consumer |
| 7 | `revenue_business` | sum of amount over valid orders whose customer segment is business |
| 8 | `top_customer_revenue` | largest per-customer sum of valid order amounts |
| 9 | `median_days_since_signup` | median (Type-7) of order_day - signup_day over valid orders |
| 10 | `repeat_customer_frac` | (customers with >= 2 valid orders) / (customers with >= 1 valid order) |
| 11 | `orders_per_customer_mean` | n_orders_valid / (customers with >= 1 valid order) |
| 12 | `max_order_amount` | largest single valid order amount |

## Submission contract

Write `artifacts/gc-395/stats.json` (path relative to the benchmark repo
root): a single JSON object mapping each of the 12 names above to a finite
number. Extra keys are ignored; missing or non-finite values count as
mismatches (fail-closed).

## Grading

    python3 assets/gc-395/grade.py

run from the repo root (stdlib-only; no third-party packages needed). The
grader verifies the sealed data hashes, recomputes all 12 statistics with an
independent implementation, cross-checks them against the sealed values, and
then compares your submission within per-statistic tolerance
`tol = max(1e-8, 1e-6 * |sealed value|)`. Its final stdout line is a JSON
object whose `stats_matched` field is the graded metric; the card passes at
`stats_matched >= 12`. A missing or malformed submission, or a tampered data
file, scores 0.
