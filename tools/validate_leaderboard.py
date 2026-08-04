#!/usr/bin/env python3
"""Validator for ``results/leaderboard.json`` (fail-closed, no network).

The submission format has always asked for the models behind a run. This makes
that ask enforceable, and adds the one field our own runs proved is needed:
**what ended each episode**.

Why the ``limits`` block exists
-------------------------------
An episode ends when it runs out of money, turns, or seconds. If turns or
seconds run out first, the resulting verdicts describe the *runner's limits*,
not the agent. We measured that on our own 26-episode ledger — wall clock ended
10, the cycle cap ended 8, a red streak ended 2, and the budget ended zero,
after spending 5.5% of the allocated budget. Nothing in a pass-rate reveals
this, so an entry has to say it out loud.

A limit-bound run is a legitimate submission. It is just a different
measurement, and the difference belongs in the entry rather than in the
reader's inference.

Usage:
  python3 tools/validate_leaderboard.py [results/leaderboard.json]

Exit code 0 = every entry valid (an empty board is valid). 1 = problems, each
printed with the index of the offending entry. 2 = the file itself is unusable.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCHEMA = "agi_benchmark_leaderboard_v1"

#: Labels for what ended an episode. Kept closed on purpose: an unknown label
#: would silently join the "we don't know" bucket, and this whole block exists
#: to keep "the agent stopped" distinguishable from "the runner stopped it".
BINDING_LIMITS = (
    "green",        # the card's success condition was reached
    "budget",       # the episode spent its allocation — the intended binding limit
    "wall_clock",   # a timeout ended it
    "cycles",       # a turn/iteration cap ended it
    "red_streak",   # consecutive failures ended it
    "aborted",      # the loop crashed, or the runner declined to start/continue
    "refused",      # the agent stopped on purpose: it judged the goal impossible
    "unknown",      # honestly unattributed — never fold this into another bucket
)
#: The labels that mean the agent's own decision or resource ended the episode.
#: ``refused`` belongs here and not with ``aborted``: recognising that a goal
#: cannot be met is a capability, and an agent that says so is not the same as
#: a loop that crashed. Folding them together makes an honest stop indis-
#: tinguishable from a traceback, which is the confusion this block exists to
#: prevent. A refusal is still checkable — the episode log must show the work
#: that led to it, and a refusal with no attempts is not a refusal.
_AGENT_BOUND = ("green", "budget", "refused")

_REQUIRED = ("agent", "submitted", "models", "cards_attempted", "outcome_pass",
             "usd", "limits", "corpus")
#: Length of a hex sha256 — the corpus id is a content hash, not a name.
_SHA256_HEX = 64
_PROCESS_AXES = ("planning", "verification", "honesty", "recovery", "autonomy",
                 "economy")


def _problems_for(i: int, e: Any) -> list[str]:
    out: list[str] = []

    def bad(msg: str) -> None:
        out.append(f"entry[{i}]: {msg}")

    if not isinstance(e, dict):
        return [f"entry[{i}]: must be an object, got {type(e).__name__}"]

    for key in _REQUIRED:
        if key not in e:
            bad(f"missing required field {key!r}")

    models = e.get("models")
    if not isinstance(models, dict) or not models:
        bad("models must be a non-empty object naming the models per role")
    elif not str(models.get("worker") or "").strip():
        # The one field a reader cannot reconstruct and cannot do without:
        # spend rate is a property of the worker, and list prices across tiers
        # differ by more than 100x. A score without it invites the reading
        # that a cheap worker's wall-clock-bound sweep is a capability result.
        bad("models.worker is required — a score without the model that "
            "produced it cannot be compared to anything")

    # The card set a result was graded against, as a content hash.
    #
    # A tag name will not do. On 2026-08-04 three released tags were withdrawn
    # and deleted; every result that named one now points at a ref that does not
    # resolve, and nobody can recover what those cards said. A hash cannot be
    # moved or deleted out from under a result — two runs agree on it exactly
    # when they graded the same text and the same asset bytes.
    #
    # `ref` is kept alongside because it is what a human types to check out, but
    # it is advisory: the hash is the identity.
    corpus = e.get("corpus")
    if not isinstance(corpus, dict):
        bad("corpus must be an object — run `python3 tools/corpus_fingerprint.py` "
            "and paste what it prints")
    else:
        digest = str(corpus.get("corpus_sha256") or "").strip().lower()
        if len(digest) != _SHA256_HEX or any(c not in "0123456789abcdef" for c in digest):
            bad("corpus.corpus_sha256 must be a hex sha256 from "
                "tools/corpus_fingerprint.py — a tag name is not durable "
                "(tags have been deleted; hashes have not)")
        n = corpus.get("cards")
        if not isinstance(n, int) or n <= 0:
            bad("corpus.cards must be the positive card count that hash covers")
        elif isinstance(e.get("cards_attempted"), int) and e["cards_attempted"] > n:
            bad(f"cards_attempted {e['cards_attempted']} exceeds corpus.cards {n} "
                "— you cannot attempt more cards than the set contains")

    n = e.get("cards_attempted")
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        bad(f"cards_attempted must be a non-negative integer, got {n!r}")
        n = None

    usd = e.get("usd")
    if isinstance(usd, bool) or not isinstance(usd, (int, float)) or usd < 0:
        bad(f"usd must be a non-negative number, got {usd!r}")

    proc = e.get("process")
    if proc is not None:
        if not isinstance(proc, dict):
            bad("process must be an object when present")
        else:
            for axis, v in proc.items():
                if axis not in _PROCESS_AXES:
                    bad(f"process axis {axis!r} is not one of {_PROCESS_AXES}")
                elif isinstance(v, bool) or not isinstance(v, (int, float)) \
                        or not 0.0 <= float(v) <= 1.0:
                    bad(f"process.{axis} must be a number in [0,1], got {v!r}")

    out += _limit_problems(i, e.get("limits"), n)
    return out


def _limit_problems(i: int, limits: Any, attempted: "int | None") -> list[str]:
    out: list[str] = []

    def bad(msg: str) -> None:
        out.append(f"entry[{i}]: {msg}")

    if limits is None:
        return out                       # already reported as a missing field
    if not isinstance(limits, dict):
        bad("limits must be an object")
        return out
    bound = limits.get("bound_by")
    if not isinstance(bound, dict) or not bound:
        bad("limits.bound_by must be a non-empty object mapping "
            f"{list(BINDING_LIMITS)} to episode counts")
        return out

    total = 0
    for label, count in bound.items():
        if label not in BINDING_LIMITS:
            bad(f"limits.bound_by has unknown label {label!r} — "
                f"allowed: {list(BINDING_LIMITS)}")
            continue
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            bad(f"limits.bound_by[{label!r}] must be a non-negative integer, "
                f"got {count!r}")
            continue
        total += count
    # Equality, not ``<=``. Over-counting is an obvious error; under-counting is
    # the dangerous one, and it used to pass: an entry could attempt 155 cards,
    # label 3, and leave 152 episodes attributed to nothing. ``agent_bound_share``
    # is then computed over the 3 that were labelled, so dropping the episodes
    # that ended badly *improves* the number. Unlabelled episodes are exactly
    # what ``unknown`` is for — the label has to be spent, not skipped.
    if attempted is not None and total != attempted:
        direction = "exceeds" if total > attempted else "falls short of"
        bad(f"limits.bound_by sums to {total} but cards_attempted is "
            f"{attempted} — the sum {direction} it. Every episode has exactly "
            f"one binding limit; use 'unknown' for the ones you cannot "
            f"attribute rather than omitting them")
    return out


def summarize(entry: dict[str, Any]) -> dict[str, Any]:
    """What a reader needs to know before comparing this entry to another.

    ``agent_bound_share`` is the fraction of episodes that ended because the
    agent succeeded or spent its allocation, rather than because the runner
    stopped them. It is not a score and is not part of validation — it is the
    context that makes a pass-rate readable.
    """
    bound = (entry.get("limits") or {}).get("bound_by") or {}
    counts = {k: v for k, v in bound.items()
              if k in BINDING_LIMITS and isinstance(v, int)
              and not isinstance(v, bool)}
    total = sum(counts.values())
    agent = sum(counts.get(k, 0) for k in _AGENT_BOUND)
    return {
        "agent": entry.get("agent"),
        "worker": (entry.get("models") or {}).get("worker"),
        "episodes_labelled": total,
        "agent_bound": agent,
        # 0 episodes labelled → None, never 0.0. "no episodes" and "no episode
        # reached its own limit" are different facts and must not share a value.
        "agent_bound_share": None if not total else round(agent / total, 3),
        "runner_bound": total - agent,
    }


def validate(path: Path) -> tuple[int, list[str], list[dict[str, Any]]]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return 2, [f"{path}: unreadable — {type(exc).__name__}: {exc}"], []
    if not isinstance(doc, dict):
        return 2, [f"{path}: top level must be an object"], []
    entries = doc.get("entries")
    if entries is None or not isinstance(entries, list):
        return 2, [f"{path}: 'entries' must be a list (an empty one is fine)"], []

    problems: list[str] = []
    for i, e in enumerate(entries):
        problems += _problems_for(i, e)
    summaries = [summarize(e) for e in entries if isinstance(e, dict)]
    return (1 if problems else 0), problems, summaries


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    path = Path(args[0]) if args else (
        Path(__file__).resolve().parents[1] / "results" / "leaderboard.json")
    code, problems, summaries = validate(path)
    for p in problems:
        print(p, file=sys.stderr)
    if code == 0:
        print(json.dumps({"schema": SCHEMA, "file": str(path),
                          "entries": len(summaries), "ok": True,
                          "summaries": summaries}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
