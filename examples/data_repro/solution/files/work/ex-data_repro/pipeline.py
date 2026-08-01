#!/usr/bin/env python3
"""Reference pipeline for ex-data_repro — the code an agent would have written.

Run from the workspace root:

    python3 work/ex-data_repro/pipeline.py

Reads assets/ex-data_repro/data.csv and writes artifacts/ex-data_repro/stats.json,
the file the sealed grader reads. Stdlib only, so the demo needs no pip install;
a real agent may use numpy/pandas as long as it pins the *definitions* the spec
requires rather than the library defaults.

The two definitions that a naive first attempt gets wrong (and that the grader
reports back by name, not by count):

  q25 / median  -> Type-7 linear interpolation. numpy.quantile defaults to
                   this; statistics.quantiles(..., n=4) does NOT (it is Type-6,
                   the exclusive method) and would miss both.
  skewness_g1   -> the BIASED Fisher-Pearson g1 (population moments). pandas
                   .skew() returns the adjusted G1 = g1 * sqrt(n(n-1))/(n-2),
                   which for n=24 is ~4.5% high — orders of magnitude outside
                   the 1e-6 relative tolerance.
"""
import csv
import json
import math
import os

DATA = os.path.join("assets", "ex-data_repro", "data.csv")
OUT = os.path.join("artifacts", "ex-data_repro", "stats.json")


def quantile_type7(sorted_xs, q):
    """Type-7 quantile: linear interpolation between order statistics."""
    h = (len(sorted_xs) - 1) * q
    lo = math.floor(h)
    hi = math.ceil(h)
    return sorted_xs[lo] + (h - lo) * (sorted_xs[hi] - sorted_xs[lo])


def main():
    with open(DATA, newline="") as fh:
        xs = [float(row["temp_c"]) for row in csv.DictReader(fh)]

    n = len(xs)
    mean = sum(xs) / n
    # sample (n-1) denominator, as the spec pins
    sample_var = sum((x - mean) ** 2 for x in xs) / (n - 1)
    # population central moments for the BIASED skewness g1
    m2 = sum((x - mean) ** 2 for x in xs) / n
    m3 = sum((x - mean) ** 3 for x in xs) / n
    s = sorted(xs)

    stats = {
        "n_rows": n,
        "mean": mean,
        "sample_std": math.sqrt(sample_var),
        "q25": quantile_type7(s, 0.25),
        "median": quantile_type7(s, 0.5),
        "skewness_g1": m3 / m2 ** 1.5,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(stats, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps({"wrote": OUT, "stats": stats}, sort_keys=True))


if __name__ == "__main__":
    main()
