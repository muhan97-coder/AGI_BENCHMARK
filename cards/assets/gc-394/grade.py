#!/usr/bin/env python3
"""Grader for gc-394 (data_repro band). Stdlib only. Fail-closed.

Run from the benchmark repo root:

    python3 assets/gc-394/grade.py

Steps: (1) verify the sealed sha256 of every bundled data file, (2) recompute
the 12 sealed statistics with an independent stdlib implementation, (3) cross-
check the recomputation against assets/gc-394/expected_stats.json, (4) compare
the submission artifacts/gc-394/stats.json value-by-value within per-statistic
tolerance. Prints exactly one JSON line; "stats_matched" is the graded metric.
Any missing/malformed input scores 0 (fail-closed).
"""
import csv
import hashlib
import json
import math
import os
import sys

CARD = "gc-394"
ASSET_DIR = os.path.join("assets", CARD)
DATA_FILES = ['data.csv']
SUBMISSION = os.path.join("artifacts", CARD, "stats.json")

def fmean(xs):
    return sum(xs) / len(xs)


def variance_sample(xs):
    m = fmean(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def std_sample(xs):
    return math.sqrt(variance_sample(xs))


def quantile_t7(xs, q):
    s = sorted(xs)
    h = (len(s) - 1) * q
    lo = math.floor(h)
    hi = math.ceil(h)
    return s[lo] + (h - lo) * (s[hi] - s[lo])


def skew_g1(xs):
    n = len(xs)
    m = fmean(xs)
    m2 = sum((x - m) ** 2 for x in xs) / n
    m3 = sum((x - m) ** 3 for x in xs) / n
    return m3 / m2 ** 1.5


def pearson(xs, ys):
    mx = fmean(xs)
    my = fmean(ys)
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    return sxy / math.sqrt(sxx * syy)


def rankdata_avg(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        r = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = r
        i = j + 1
    return ranks


def spearman(xs, ys):
    return pearson(rankdata_avg(xs), rankdata_avg(ys))


def ols_slope_intercept(xs, ys):
    mx = fmean(xs)
    my = fmean(ys)
    sxx = sum((a - mx) ** 2 for a in xs)
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    slope = sxy / sxx
    return slope, my - slope * mx


def jacobi_eigenvalues(mat):
    n = len(mat)
    a = [row[:] for row in mat]
    for _ in range(500):
        p, q, mx = 0, 1, 0.0
        for i in range(n):
            for j in range(i + 1, n):
                if abs(a[i][j]) > mx:
                    mx, p, q = abs(a[i][j]), i, j
        if mx < 1e-13:
            break
        app, aqq, apq = a[p][p], a[q][q], a[p][q]
        tau = (aqq - app) / (2.0 * apq)
        t = (1.0 if tau >= 0 else -1.0) / (abs(tau) + math.sqrt(1.0 + tau * tau))
        c = 1.0 / math.sqrt(1.0 + t * t)
        s = t * c
        a[p][p] = app - t * apq
        a[q][q] = aqq + t * apq
        a[p][q] = a[q][p] = 0.0
        for k in range(n):
            if k != p and k != q:
                akp, akq = a[k][p], a[k][q]
                a[k][p] = a[p][k] = c * akp - s * akq
                a[k][q] = a[q][k] = s * akp + c * akq
    return sorted((a[i][i] for i in range(n)), reverse=True)

def compute_stats(tables):
    rows = tables["data.csv"]
    xs = [float(r["x"]) for r in rows]
    ys = [float(r["y"]) for r in rows]
    n = len(xs)

    def tmean(v):
        s = sorted(v)
        k = int(math.floor(0.1 * len(v)))
        return fmean(s[k:len(s) - k])

    full_r = pearson(xs, ys)
    loo_means, loo_meds, loo_trs, loo_rs = [], [], [], []
    for i in range(n):
        rx = xs[:i] + xs[i + 1:]
        ry = ys[:i] + ys[i + 1:]
        loo_means.append(fmean(rx))
        loo_meds.append(quantile_t7(rx, 0.5))
        loo_trs.append(tmean(rx))
        loo_rs.append(pearson(rx, ry))

    def jse(loo):
        mb = fmean(loo)
        return math.sqrt((n - 1) / n * sum((v - mb) ** 2 for v in loo))

    return {
        "n_rows": float(n),
        "mean_x": fmean(xs),
        "median_x": quantile_t7(xs, 0.5),
        "trimmed_mean_x_10": tmean(xs),
        "jackknife_se_mean_x": jse(loo_means),
        "jackknife_se_median_x": jse(loo_meds),
        "jackknife_se_trimmed_x": jse(loo_trs),
        "pearson_xy": full_r,
        "jackknife_se_pearson_xy": jse(loo_rs),
        "jackknife_bias_pearson_xy": (n - 1) * (fmean(loo_rs) - full_r),
        "max_abs_influence_pearson": max(abs(v - full_r) for v in loo_rs),
        "min_loo_pearson": min(loo_rs),
    }


def emit(obj):
    print(json.dumps(obj, sort_keys=True))
    sys.exit(0)


def main():
    try:
        with open(os.path.join(ASSET_DIR, "expected_stats.json")) as f:
            expected = json.load(f)
    except Exception as exc:
        emit({"stats_matched": 0, "stats_total": 12,
              "error": "expected_stats unreadable: %s" % exc})
    names = sorted(expected["stats"])
    tables = {}
    for fname in DATA_FILES:
        path = os.path.join(ASSET_DIR, fname)
        try:
            with open(path, "rb") as f:
                blob = f.read()
        except Exception as exc:
            emit({"stats_matched": 0, "stats_total": len(names),
                  "error": "data file unreadable: %s" % exc})
        if hashlib.sha256(blob).hexdigest() != expected["data_sha256"][fname]:
            emit({"stats_matched": 0, "stats_total": len(names),
                  "error": "data_hash_mismatch:%s" % fname})
        with open(path, newline="") as f:
            tables[fname] = list(csv.DictReader(f))
    recomputed = compute_stats(tables)
    for k in names:
        if abs(recomputed[k] - expected["stats"][k]["value"]) > expected["stats"][k]["tol"]:
            emit({"stats_matched": 0, "stats_total": len(names),
                  "error": "grader_recompute_mismatch:%s" % k})
    try:
        with open(SUBMISSION) as f:
            sub = json.load(f)
    except Exception as exc:
        emit({"stats_matched": 0, "stats_total": len(names), "matched": [],
              "mismatched": [], "missing": names,
              "error": "submission unreadable: %s" % exc})
    if not isinstance(sub, dict):
        emit({"stats_matched": 0, "stats_total": len(names), "matched": [],
              "mismatched": [], "missing": names,
              "error": "submission is not a JSON object"})
    matched, mismatched, missing = [], [], []
    for k in names:
        if k not in sub:
            missing.append(k)
            continue
        try:
            v = float(sub[k])
        except (TypeError, ValueError):
            mismatched.append(k)
            continue
        if math.isfinite(v) and abs(v - recomputed[k]) <= expected["stats"][k]["tol"]:
            matched.append(k)
        else:
            mismatched.append(k)
    emit({"stats_matched": len(matched), "stats_total": len(names),
          "mismatched": mismatched, "missing": missing})


if __name__ == "__main__":
    main()
