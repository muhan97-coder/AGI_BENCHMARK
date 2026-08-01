#!/usr/bin/env python3
"""Regenerate the gc-389 dataset byte-identically (stdlib only, fixed seed).

Run from the benchmark repo root:

    python3 assets/gc-389/make_dataset.py

Rewrites data.csv under assets/gc-389/. The sha256 of each data file is
sealed in assets/gc-389/expected_stats.json; regeneration must reproduce it.
"""
import math
import os
import random

def generate():
    rng = random.Random(38906)
    rows = []
    for i in range(500):
        f1 = rng.gauss(0.0, 1.0)
        f2 = rng.gauss(0.0, 1.0)
        a = f1 + 0.3 * rng.gauss(0.0, 1.0)
        b = 0.8 * f1 + 0.5 * f2 + 0.4 * rng.gauss(0.0, 1.0)
        c = -0.6 * f1 + 0.7 * f2 + 0.5 * rng.gauss(0.0, 1.0)
        d = 0.2 * f1 - 0.5 * f2 + 0.6 * rng.gauss(0.0, 1.0)
        rows.append(["N%04d" % i] + [format(v, ".5f") for v in (a, b, c, d)])
    return {"data.csv": (["row_id", "a", "b", "c", "d"], rows)}


def main():
    outdir = os.path.join("assets", "gc-389")
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
