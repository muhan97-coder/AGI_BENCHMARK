#!/usr/bin/env python3
"""Regenerate the gc-394 dataset byte-identically (stdlib only, fixed seed).

Run from the benchmark repo root:

    python3 assets/gc-394/make_dataset.py

Rewrites data.csv under assets/gc-394/. The sha256 of each data file is
sealed in assets/gc-394/expected_stats.json; regeneration must reproduce it.
"""
import math
import os
import random

def generate():
    rng = random.Random(39411)
    rows = []
    for i in range(240):
        x = rng.gauss(50.0, 8.0)
        if rng.random() < 0.03:
            x += rng.uniform(15.0, 30.0)
        y = 10.0 + 0.7 * x + rng.gauss(0.0, 5.0)
        rows.append(["J%03d" % i, format(x, ".4f"), format(y, ".4f")])
    return {"data.csv": (["row_id", "x", "y"], rows)}


def main():
    outdir = os.path.join("assets", "gc-394")
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
