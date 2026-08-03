#!/usr/bin/env python3
"""Compute a durable identity for the card set a result was produced against.

## Why a hash and not a tag name

On 2026-08-04 three released tags — `v1.0-alpha`, `v1.0-beta`, `v2-alpha` — were
withdrawn and **deleted from the repository**. Anyone holding a result that says
"run against v2-alpha" now points at a ref that no longer resolves, and nobody can
check what those 155 cards actually said at the time. A tag is a mutable label:
it can be moved, deleted, or re-cut on a different commit, and none of those
leave a trace in a result file.

A content hash cannot do any of that. `corpus_sha256` below is a function of the
card text and the asset bytes, so two runs agree on it if and only if they graded
the same thing — whatever the tag was called that week.

## What is hashed

Each card contributes its **canonical JSON** (sorted keys, no insignificant
whitespace) so that a reformat is not mistaken for a content change, plus the
sha256 of every asset file under `cards/assets/<id>/`, sorted by name. Cards are
folded in id order. Sealed assets are hashed like any other file — the point is
identity, not secrecy, and a run that received a different answer file must not
report the same corpus id.

## What is deliberately excluded

The dashboard (`docs/`), the tools, and the prose all change without changing
what an agent is asked to do. Folding them in would make every README edit look
like a new corpus and train readers to ignore the field.

Usage:

    python3 tools/corpus_fingerprint.py                # summary for a submission
    python3 tools/corpus_fingerprint.py --per-card     # one line per card
    python3 tools/corpus_fingerprint.py --json         # machine-readable
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CARDS_DIR = ROOT / "cards"
ASSETS_DIR = CARDS_DIR / "assets"
SCHEMA = "agi_benchmark_corpus_fingerprint_v1"


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _canonical(card: dict[str, Any]) -> bytes:
    """Card text with formatting removed — a reindent must not read as a change."""
    return json.dumps(card, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def _asset_digest(card_id: str) -> tuple[str, int]:
    """(digest over this card's asset tree, file count). No assets → empty digest."""
    d = ASSETS_DIR / card_id
    if not d.is_dir():
        return "", 0
    h = hashlib.sha256()
    n = 0
    for p in sorted(d.rglob("*")):
        if not p.is_file():
            continue
        h.update(str(p.relative_to(d)).encode("utf-8"))
        h.update(b"\0")
        h.update(_sha256_bytes(p.read_bytes()).encode("ascii"))
        n += 1
    return h.hexdigest(), n


def fingerprint() -> dict[str, Any]:
    cards: list[dict[str, Any]] = []
    for f in sorted(CARDS_DIR.glob("gc-*.json")):
        card = json.loads(f.read_text())
        cid = str(card.get("id") or f.stem)
        adig, acount = _asset_digest(cid)
        cards.append({
            "id": cid,
            "card_sha256": _sha256_bytes(_canonical(card)),
            "assets_sha256": adig,
            "assets_files": acount,
        })
    cards.sort(key=lambda c: c["id"])
    roll = hashlib.sha256()
    for c in cards:
        roll.update(c["id"].encode("utf-8"))
        roll.update(b"\0")
        roll.update(c["card_sha256"].encode("ascii"))
        roll.update(b"\0")
        roll.update(c["assets_sha256"].encode("ascii"))
        roll.update(b"\n")
    return {"schema": SCHEMA, "cards": len(cards),
            "corpus_sha256": roll.hexdigest(), "per_card": cards}


def main(argv: list[str]) -> int:
    fp = fingerprint()
    if "--json" in argv:
        print(json.dumps(fp, ensure_ascii=False, indent=1))
        return 0
    if "--per-card" in argv:
        for c in fp["per_card"]:
            print(f"{c['id']}  card={c['card_sha256'][:16]}  "
                  f"assets={c['assets_sha256'][:16] or '-':16s}  "
                  f"files={c['assets_files']}")
        print()
    print(f"cards          {fp['cards']}")
    print(f"corpus_sha256  {fp['corpus_sha256']}")
    print()
    print("Put this in your leaderboard entry so the result stays checkable even")
    print("if the tag it was cut from is later moved or deleted:")
    print()
    print(json.dumps({"corpus": {"cards": fp["cards"],
                                 "corpus_sha256": fp["corpus_sha256"],
                                 "ref": "<tag or commit you checked out>"}},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
