#!/usr/bin/env python3
"""Regenerate the gc-385 dataset byte-identically (stdlib only, fixed seed).

Run from the benchmark repo root:

    python3 assets/gc-385/make_dataset.py

Rewrites data.csv under assets/gc-385/. The sha256 of each data file is
sealed in assets/gc-385/expected_stats.json; regeneration must reproduce it.
"""
import math
import os
import random

def generate():
    rng = random.Random(38502)
    rows = []
    sid = 0
    for _ in range(420):
        rows.append(["S%04d" % sid, "A", format(math.exp(rng.gauss(4.60, 0.35)), ".3f")])
        sid += 1
    for _ in range(380):
        rows.append(["S%04d" % sid, "B", format(math.exp(rng.gauss(4.52, 0.40)), ".3f")])
        sid += 1
    return {"data.csv": (["sample_id", "group", "latency_ms"], rows)}


def main():
    outdir = os.path.join("assets", "gc-385")
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
