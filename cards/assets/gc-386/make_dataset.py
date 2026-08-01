#!/usr/bin/env python3
"""Regenerate the gc-386 dataset byte-identically (stdlib only, fixed seed).

Run from the benchmark repo root:

    python3 assets/gc-386/make_dataset.py

Rewrites data.csv under assets/gc-386/. The sha256 of each data file is
sealed in assets/gc-386/expected_stats.json; regeneration must reproduce it.
"""
import math
import os
import random

def generate():
    rng = random.Random(38603)
    cats = ["view", "click", "login", "search", "purchase", "share",
            "comment", "logout", "upload", "download", "refund", "invite"]
    weights = [30.0, 22.0, 15.0, 11.0, 8.0, 6.0, 5.0, 4.0, 3.0, 2.5, 1.5, 1.0]
    tot = sum(weights)
    cum = []
    acc = 0.0
    for w in weights:
        acc += w
        cum.append(acc / tot)
    rows = []
    for i in range(523):
        r = rng.random()
        for c, cv in zip(cats, cum):
            if r <= cv:
                rows.append(["E%04d" % i, c])
                break
    return {"data.csv": (["event_id", "category"], rows)}


def main():
    outdir = os.path.join("assets", "gc-386")
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
