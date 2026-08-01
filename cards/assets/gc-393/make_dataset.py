#!/usr/bin/env python3
"""Regenerate the gc-393 dataset byte-identically (stdlib only, fixed seed).

Run from the benchmark repo root:

    python3 assets/gc-393/make_dataset.py

Rewrites data.csv under assets/gc-393/. The sha256 of each data file is
sealed in assets/gc-393/expected_stats.json; regeneration must reproduce it.
"""
import math
import os
import random

def generate():
    rng = random.Random(39310)
    pts = []
    blobs = [((0.0, 0.0), 1.5, 120), ((3.2, 2.2), 1.6, 150), ((-2.2, 4.2), 1.4, 130)]
    for (cx, cy), sd, m in blobs:
        for _ in range(m):
            pts.append((cx + rng.gauss(0.0, sd), cy + rng.gauss(0.0, sd)))
    rng.shuffle(pts)
    rows = [["K%04d" % i, format(x, ".4f"), format(y, ".4f")]
            for i, (x, y) in enumerate(pts)]
    return {"data.csv": (["point_id", "px", "py"], rows)}


def main():
    outdir = os.path.join("assets", "gc-393")
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
