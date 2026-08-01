#!/usr/bin/env python3
"""Regenerate the gc-388 dataset byte-identically (stdlib only, fixed seed).

Run from the benchmark repo root:

    python3 assets/gc-388/make_dataset.py

Rewrites data.csv under assets/gc-388/. The sha256 of each data file is
sealed in assets/gc-388/expected_stats.json; regeneration must reproduce it.
"""
import math
import os
import random

def generate():
    rng = random.Random(38805)
    dow = [0.0, 1.2, 2.5, 1.8, 0.6, -2.2, -3.1]
    e = 0.0
    rows = []
    for t in range(730):
        e = 0.6 * e + rng.gauss(0.0, 1.5)
        v = 50.0 + 0.02 * t + dow[t % 7] + e
        rows.append([str(t), format(v, ".4f")])
    return {"data.csv": (["day_index", "value"], rows)}


def main():
    outdir = os.path.join("assets", "gc-388")
    os.makedirs(outdir, exist_ok=True)
    for fname, (fields, rows) in sorted(generate().items()):
        path = os.path.join(outdir, fname)
        with open(path, "w", newline="") as f:
            f.write(",".join(fields) + "\n")
            for row in rows:
                f.write(",".join(row) + "\n")
        print("wrote %s (%d rows)" % (path, len(rows)))


if __name__ == "__main__":
    main()
