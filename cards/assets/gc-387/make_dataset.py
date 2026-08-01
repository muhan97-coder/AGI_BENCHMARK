#!/usr/bin/env python3
"""Regenerate the gc-387 dataset byte-identically (stdlib only, fixed seed).

Run from the benchmark repo root:

    python3 assets/gc-387/make_dataset.py

Rewrites data.csv under assets/gc-387/. The sha256 of each data file is
sealed in assets/gc-387/expected_stats.json; regeneration must reproduce it.
"""
import math
import os
import random

def generate():
    rng = random.Random(38704)
    rows = []
    for i in range(640):
        x = rng.uniform(0.0, 100.0)
        y = 3.2 + 0.85 * x + rng.gauss(0.0, 6.0)
        rows.append(["P%04d" % i, format(x, ".3f"), format(y, ".3f")])
    return {"data.csv": (["obs_id", "x", "y"], rows)}


def main():
    outdir = os.path.join("assets", "gc-387")
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
