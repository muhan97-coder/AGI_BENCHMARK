#!/usr/bin/env python3
"""Regenerate the gc-391 dataset byte-identically (stdlib only, fixed seed).

Run from the benchmark repo root:

    python3 assets/gc-391/make_dataset.py

Rewrites data.csv under assets/gc-391/. The sha256 of each data file is
sealed in assets/gc-391/expected_stats.json; regeneration must reproduce it.
"""
import math
import os
import random

def generate():
    rng = random.Random(39108)
    plan = [("alpha", 140, 72.0), ("beta", 170, 74.5),
            ("gamma", 155, 71.0), ("delta", 185, 76.0)]
    rows = []
    uid = 0
    for gname, gn, base in plan:
        for _ in range(gn):
            rows.append(["U%04d" % uid, gname, format(base + rng.gauss(0.0, 3.0), ".3f")])
            uid += 1
    return {"data.csv": (["unit_id", "machine", "yield_pct"], rows)}


def main():
    outdir = os.path.join("assets", "gc-391")
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
