#!/usr/bin/env python3
"""Deterministic regeneration of the ex-data_repro dataset (stdlib only).

Run from the workspace root:

    python3 assets/ex-data_repro/make_dataset.py

Rewrites assets/ex-data_repro/data.csv byte-identically on every platform:
fixed seed, Mersenne Twister, values rounded to 2 decimals before formatting.
24 temperature readings from a synthetic sensor, with three injected heat
spikes so the distribution is right-skewed (which is what makes the biased
skewness definition worth pinning).
"""
import os
import random

SEED = 20260802
N_ROWS = 24
SPIKE_AT = (7, 15, 20)
OUT = os.path.join("assets", "ex-data_repro", "data.csv")


def rows():
    rng = random.Random(SEED)
    for i in range(N_ROWS):
        base = 18.0 + 4.0 * rng.random()
        if i in SPIKE_AT:
            base += 9.0 + 6.0 * rng.random()
        yield i + 1, round(base, 2)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    lines = ["reading_id,temp_c"]
    for rid, temp in rows():
        lines.append("%d,%.2f" % (rid, temp))
    with open(OUT, "w", newline="") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote %s (%d rows)" % (OUT, N_ROWS))


if __name__ == "__main__":
    main()
