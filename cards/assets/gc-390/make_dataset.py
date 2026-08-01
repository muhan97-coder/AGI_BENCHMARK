#!/usr/bin/env python3
"""Regenerate the gc-390 dataset byte-identically (stdlib only, fixed seed).

Run from the benchmark repo root:

    python3 assets/gc-390/make_dataset.py

Rewrites data.csv under assets/gc-390/. The sha256 of each data file is
sealed in assets/gc-390/expected_stats.json; regeneration must reproduce it.
"""
import math
import os
import random

def generate():
    rng = random.Random(39007)
    rows = []
    for i in range(600):
        x = rng.gauss(10.0, 2.0)
        y = 3.0 + 0.5 * x + rng.gauss(0.0, 1.0)
        z = rng.uniform(0.0, 20.0)
        xs = "" if rng.random() < 0.08 else format(x, ".4f")
        ys = "" if rng.random() < 0.12 else format(y, ".4f")
        zs = "" if rng.random() < 0.05 else format(z, ".4f")
        rows.append(["R%04d" % i, xs, ys, zs])
    return {"data.csv": (["row_id", "x", "y", "z"], rows)}


def main():
    outdir = os.path.join("assets", "gc-390")
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
