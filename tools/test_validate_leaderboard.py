#!/usr/bin/env python3
"""Tests for the leaderboard validator's closed label vocabulary.

The vocabulary is the only part of a submission a reader cannot check by
re-running a grader — a wrong label produces a plausible number. So it is
worth proving that the validator both **accepts** the labels it documents and
**rejects** anything else.

A test that only builds a valid entry and asserts "no problems" proves nothing:
it would still pass if ``_limit_problems`` returned ``[]`` unconditionally.
Every case here therefore comes in two arms — one that must pass and one that
must fail — so a gate that stopped firing shows up as a failure, not a silence.

Run: python3 -m pytest tools/test_validate_leaderboard.py -q
     (or: python3 tools/test_validate_leaderboard.py)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_leaderboard import (  # noqa: E402
    BINDING_LIMITS,
    _AGENT_BOUND,
    summarize,
    validate,
)

_SHA = "a" * 64


def _entry(bound_by: dict[str, int], **over):
    """A minimally valid entry whose episode labels sum to cards_attempted."""
    e = {
        "agent": "test-agent",
        "submitted": "2026-08-04",
        "models": {"planner": "m-p", "worker": "m-w", "reviewer": "m-r"},
        "cards_attempted": sum(bound_by.values()),
        "outcome_pass": f"{bound_by.get('green', 0)}/{sum(bound_by.values())}",
        "usd": 1.0,
        "limits": {"bound_by": dict(bound_by)},
        "corpus": {"cards": sum(bound_by.values()), "corpus_sha256": _SHA},
    }
    e.update(over)
    return e


def _run(entries, tmp_path) -> tuple[int, list[str], list[dict]]:
    p = tmp_path / "board.json"
    p.write_text(json.dumps({"schema": "agi_benchmark_leaderboard_v1",
                             "entries": entries}), encoding="utf-8")
    return validate(p)


# ───────────────── vocabulary: accepted vs rejected (two arms) ─────────────────


def test_every_documented_label_is_accepted(tmp_path):
    """Arm 1 — each label in BINDING_LIMITS passes on its own."""
    for label in BINDING_LIMITS:
        code, problems, _ = _run([_entry({label: 3})], tmp_path)
        assert code == 0, f"{label!r} should be a valid label but: {problems}"


def test_an_undocumented_label_is_rejected(tmp_path):
    """Arm 2 — the gate must FIRE. Without this, arm 1 proves nothing."""
    code, problems, _ = _run([_entry({"timed_out": 3})], tmp_path)
    assert code == 1, "an unknown binding label was accepted — the gate is dead"
    assert any("timed_out" in p for p in problems), problems


def test_refused_is_a_label(tmp_path):
    """The 8th label — added 2026-08-04. An agent that recognises an impossible
    goal and stops is not the same as one whose loop crashed."""
    assert "refused" in BINDING_LIMITS
    code, problems, _ = _run([_entry({"green": 2, "refused": 1})], tmp_path)
    assert code == 0, problems


# ───────────────── agent-bound share: refused counts toward it ─────────────────


def test_refused_counts_as_agent_bound():
    assert "refused" in _AGENT_BOUND, (
        "recognising an impossible goal is a capability — if this drops out of "
        "_AGENT_BOUND, an honest stop is scored as a runner-bound episode")
    s = summarize(_entry({"green": 1, "budget": 1, "refused": 2, "cycles": 4}))
    assert s["episodes_labelled"] == 8
    assert s["agent_bound"] == 4          # green + budget + refused
    assert s["runner_bound"] == 4         # cycles
    assert s["agent_bound_share"] == 0.5


def test_aborted_is_not_agent_bound():
    """The distinction the split exists for: a crash is not a decision."""
    assert "aborted" not in _AGENT_BOUND
    s = summarize(_entry({"refused": 1, "aborted": 1}))
    assert s["agent_bound"] == 1, "aborted leaked into the agent-bound share"


# ───────────────── the label set stays closed ─────────────────


def test_vocabulary_has_no_duplicates_and_is_closed():
    assert len(BINDING_LIMITS) == len(set(BINDING_LIMITS))
    assert set(_AGENT_BOUND) <= set(BINDING_LIMITS), (
        "an agent-bound label that is not a valid label can never be counted")


def test_unknown_stays_out_of_agent_bound():
    """`unknown` must never be folded into a neighbour — including this one."""
    assert "unknown" not in _AGENT_BOUND
    s = summarize(_entry({"green": 1, "unknown": 1}))
    assert s["agent_bound_share"] == 0.5


# ───────────────── counts must still reconcile ─────────────────


def test_labels_must_sum_to_cards_attempted(tmp_path):
    ok, problems, _ = _run([_entry({"green": 2, "refused": 1})], tmp_path)
    assert ok == 0, problems
    # Raise the corpus size too, or an earlier guard (cards_attempted >
    # corpus.cards) fires first and this test would pass without ever
    # exercising the sum check it claims to.
    bad = _entry({"green": 2, "refused": 1})
    bad["cards_attempted"] = 99
    bad["corpus"] = {"cards": 200, "corpus_sha256": _SHA}
    code, problems, _ = _run([bad], tmp_path)
    assert code == 1, "a sum mismatch was accepted"
    assert any("sums to" in p for p in problems), problems


def test_under_counting_is_rejected_not_just_over_counting(tmp_path):
    """Regression: the check used to be ``total > attempted``.

    Under that rule an entry could attempt 155 cards, label 3, and leave 152
    episodes attributed to nothing — and ``agent_bound_share`` would then be
    computed over the 3, so dropping the bad episodes *improved* the score.
    """
    under = _entry({"green": 3})
    under["cards_attempted"] = 155
    under["outcome_pass"] = "3/155"
    under["corpus"] = {"cards": 200, "corpus_sha256": _SHA}
    code, problems, _ = _run([under], tmp_path)
    assert code == 1, "under-counted labels were accepted — 152 episodes vanish"
    assert any("falls short of" in p for p in problems), problems


def test_unknown_is_the_documented_way_to_reconcile(tmp_path):
    """The rejection above must be fixable without lying: spend `unknown`."""
    fixed = _entry({"green": 3, "unknown": 152})
    fixed["cards_attempted"] = 155
    fixed["outcome_pass"] = "3/155"
    fixed["corpus"] = {"cards": 200, "corpus_sha256": _SHA}
    code, problems, _ = _run([fixed], tmp_path)
    assert code == 0, problems
    assert summarize(fixed)["agent_bound_share"] == round(3 / 155, 3)


def test_zero_episodes_gives_none_not_zero():
    """"no episodes" and "no episode reached its own limit" are different facts."""
    s = summarize({"limits": {"bound_by": {}}})
    assert s["agent_bound_share"] is None


if __name__ == "__main__":
    import subprocess
    raise SystemExit(subprocess.call(
        [sys.executable, "-m", "pytest", __file__, "-q"]))
