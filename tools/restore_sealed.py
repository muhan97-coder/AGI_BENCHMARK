#!/usr/bin/env python3
"""Restore sealed (grader-only) asset files from a sealed pack.

Cards tagged ``contamination_risk: answers_sealed`` reference grader-side
answer files that are NOT in this repository — only their ``<name>.sha256``
commitments are. Graders need the real files; agents must never see them.

Usage:
  python3 tools/restore_sealed.py --sealed-dir /path/to/sealed_pack

The sealed pack layout is ``<sealed-dir>/<card-id>/<file>``. Every restored
file is verified against its committed sha256 — a mismatch aborts (fail-closed:
a tampered or wrong answer file must never grade anything).
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "cards" / "assets"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sealed-dir", required=True)
    args = ap.parse_args()
    sealed = Path(args.sealed_dir)
    restored, missing = 0, []
    for commit in sorted(ASSETS.glob("*/*.sha256")):
        card_id = commit.parent.name
        name = commit.name[: -len(".sha256")]
        src = sealed / card_id / name
        want = commit.read_text().strip()
        if not src.is_file():
            missing.append(f"{card_id}/{name}")
            continue
        got = hashlib.sha256(src.read_bytes()).hexdigest()
        if got != want:
            print(f"ABORT: sha256 mismatch for {card_id}/{name} "
                  f"(sealed pack file does not match the committed hash)",
                  file=sys.stderr)
            return 2
        (commit.parent / name).write_bytes(src.read_bytes())
        restored += 1
    print(f"restored {restored} sealed files"
          + (f"; MISSING from pack: {missing}" if missing else ""))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
