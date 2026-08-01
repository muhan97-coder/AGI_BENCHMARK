#!/usr/bin/env python3
"""Assemble an agent-facing workspace for one card (oracle isolation).

Copies the card JSON and its TASK assets into a destination directory,
excluding sealed (grader-only) files and their sha256 commitments. Point your
agent at the destination — never at this repository — so answer-bearing files
are structurally out of reach.

Usage:
  python3 tools/assemble_workspace.py cards/gc-384_<...>.json /tmp/ws-gc-384
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("card")
    ap.add_argument("dest")
    args = ap.parse_args()
    card_path = Path(args.card)
    card = json.loads(card_path.read_text())
    sealed = set((card.get("assets_visibility") or {}).get("sealed") or [])
    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(card_path, dest / card_path.name)
    src = ROOT / "cards" / "assets" / str(card["id"])
    copied, excluded = 0, 0
    if src.is_dir():
        out = dest / "assets" / str(card["id"])
        for f in sorted(src.rglob("*")):
            if not f.is_file():
                continue
            if f.name in sealed or f.name.endswith(".sha256"):
                excluded += 1
                continue
            rel = f.relative_to(src)
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out / rel)
            copied += 1
    print(json.dumps({"card": card["id"], "workspace": str(dest),
                      "task_files": copied, "sealed_excluded": excluded}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
