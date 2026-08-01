#!/usr/bin/env python3
"""Regenerate the gc-392 dataset byte-identically (stdlib only, fixed seed).

Run from the benchmark repo root:

    python3 assets/gc-392/make_dataset.py

Rewrites data.csv under assets/gc-392/. The sha256 of each data file is
sealed in assets/gc-392/expected_stats.json; regeneration must reproduce it.
"""
import math
import os
import random

def generate():
    rng = random.Random(39209)
    rows = []
    for i in range(450):
        f1 = rng.gauss(0.0, 1.0)
        f2 = rng.gauss(0.0, 1.0)
        m1 = 0.9 * f1 + 0.35 * rng.gauss(0.0, 1.0)
        m2 = 0.85 * f1 + 0.4 * rng.gauss(0.0, 1.0)
        m3 = 0.75 * f2 + 0.5 * rng.gauss(0.0, 1.0)
        m4 = -0.55 * f2 + 0.65 * rng.gauss(0.0, 1.0)
        rows.append(["V%04d" % i] + [format(v, ".5f") for v in (m1, m2, m3, m4)])
    return {"data.csv": (["row_id", "m1", "m2", "m3", "m4"], rows)}


def main():
    outdir = os.path.join("assets", "gc-392")
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
