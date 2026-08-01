#!/usr/bin/env python3
"""Regenerate the gc-384 dataset byte-identically (stdlib only, fixed seed).

Run from the benchmark repo root:

    python3 assets/gc-384/make_dataset.py

Rewrites data.csv under assets/gc-384/. The sha256 of each data file is
sealed in assets/gc-384/expected_stats.json; regeneration must reproduce it.
"""
import math
import os
import random

def generate():
    rng = random.Random(38401)
    rows = []
    for i in range(900):
        v = 21.5 + rng.gauss(0.0, 1.8)
        if rng.random() < 0.04:
            v += rng.uniform(4.0, 9.0)
        rows.append(["R%04d" % i, format(v, ".4f")])
    return {"data.csv": (["reading_id", "temp_c"], rows)}


def main():
    outdir = os.path.join("assets", "gc-384")
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
