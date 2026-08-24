#!/usr/bin/env python3
"""Assemble an agent-facing workspace for one card (oracle isolation).

Copies the card JSON and its TASK assets into a destination directory,
excluding hidden sealed files and their sha256 commitments. Public grader
programs remain available for iterative candidate use, but are copied
read-only and recorded through the canonical grading-surface policy.

Usage:
  python3 tools/assemble_workspace.py cards/gc-384_<...>.json /tmp/ws-gc-384
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import sys
from pathlib import Path

try:
    from grading_surface import (
        SurfaceError,
        read_canonical_assets,
        restore_assets,
        validate_grader_authority,
        verify_assets,
    )
except ModuleNotFoundError:  # importable as tools.assemble_workspace in tests
    from tools.grading_surface import (
        SurfaceError,
        read_canonical_assets,
        restore_assets,
        validate_grader_authority,
        verify_assets,
    )

ROOT = Path(__file__).resolve().parent.parent


def _empty_destination(dest: Path) -> None:
    try:
        info = os.lstat(dest)
    except FileNotFoundError:
        dest.mkdir(parents=True)
        return
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise SurfaceError("workspace destination is not a real directory")
    if any(dest.iterdir()):
        raise SurfaceError("workspace destination must be empty")


def assemble(card_path: str | Path, dest: str | Path, *,
             repo_root: str | Path = ROOT) -> dict[str, object]:
    """Build one clean workspace and return a non-sensitive copy summary."""
    card_path = Path(card_path)
    card = json.loads(card_path.read_text(encoding="utf-8"))
    card_id = str(card["id"])
    grader_relpaths = validate_grader_authority(card)
    visibility = card.get("assets_visibility") or {}
    hidden = set(visibility.get("sealed") or [])
    src = Path(repo_root) / "cards" / "assets" / card_id
    canonical = read_canonical_assets(src, grader_relpaths) if grader_relpaths else ()

    dest = Path(dest)
    _empty_destination(dest)
    shutil.copy2(card_path, dest / card_path.name)
    copied, excluded = 0, 0
    if src.is_dir():
        out = dest / "assets" / card_id
        for entry in sorted(src.rglob("*")):
            info = os.lstat(entry)
            if stat.S_ISLNK(info.st_mode) or not (
                    stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                raise SurfaceError("asset tree contains a link or special file")
            if stat.S_ISDIR(info.st_mode):
                continue
            rel = entry.relative_to(src)
            if rel.as_posix() in grader_relpaths:
                continue
            if entry.name in hidden or entry.name.endswith(".sha256"):
                excluded += 1
                continue
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry, out / rel)
            copied += 1

    if canonical:
        restore_assets(dest, card_id, canonical)
        verify_assets(dest, card_id, canonical)
    return {"card": card_id, "workspace": str(dest), "task_files": copied,
            "grader_sealed": len(canonical), "sealed_excluded": excluded}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("card")
    ap.add_argument("dest")
    args = ap.parse_args()
    try:
        result = assemble(args.card, args.dest)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, SurfaceError):
        print(json.dumps({"ok": False, "error": "workspace assembly failed"}),
              file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
