#!/usr/bin/env python3
"""Regenerate the gc-395 dataset byte-identically (stdlib only, fixed seed).

Run from the benchmark repo root:

    python3 assets/gc-395/make_dataset.py

Rewrites customers.csv and orders.csv under assets/gc-395/. The sha256 of each data file is
sealed in assets/gc-395/expected_stats.json; regeneration must reproduce it.
"""
import math
import os
import random

def generate():
    rng = random.Random(39512)
    crows = []
    for i in range(90):
        cid = "C%03d" % (i + 1)
        seg = "consumer" if rng.random() < 0.6 else "business"
        crows.append([cid, seg, str(rng.randrange(0, 200))])
    orows = []
    for i in range(700):
        if rng.random() < 0.92:
            cid = "C%03d" % (rng.randrange(0, 90) + 1)
        else:
            cid = "C%03d" % rng.randrange(900, 960)
        amount = format(math.exp(rng.gauss(3.5, 0.7)), ".2f")
        orows.append(["O%04d" % i, cid, amount, str(rng.randrange(0, 365))])
    return {"customers.csv": (["customer_id", "segment", "signup_day"], crows),
            "orders.csv": (["order_id", "customer_id", "amount", "order_day"], orows)}


def main():
    outdir = os.path.join("assets", "gc-395")
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
