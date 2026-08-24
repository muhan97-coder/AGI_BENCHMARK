#!/usr/bin/env python3
"""Canonical grader-command surface and safe grader-asset restoration.

``assets_visibility.sealed`` remains reserved for hidden/private assets.
``assets_visibility.grader_sealed`` names public grader programs which are
available while a candidate iterates, but are restored from this checkout
immediately before final grading.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import stat
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
GRADER_BASENAMES = frozenset({"grade.py", "check.sh", "test_accept.py"})
EXPECTED_CENSUS = {
    "cards": 167,
    "grader_surface": 120,
    "grade_or_check": 96,
    "self_report": 12,
}
MAX_GRADER_BYTES = 2 * 1024 * 1024
_ASSET_REF = re.compile(r"assets/(?P<path>[A-Za-z0-9_.+@/-]+)")
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
_CLOEXEC = getattr(os, "O_CLOEXEC", 0)


class SurfaceError(RuntimeError):
    """The declared or on-disk grading surface is unsafe or inconsistent."""


@dataclass(frozen=True)
class CanonicalAsset:
    relpath: str
    data: bytes
    sha256: str
    mode: int


def _safe_rel(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise SurfaceError("grader asset path is invalid")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise SurfaceError("grader asset path is invalid")
    normalized = path.as_posix()
    if normalized != value:
        raise SurfaceError("grader asset path is not canonical")
    return normalized


def _string_set(visibility: dict[str, Any], field: str) -> set[str]:
    raw = visibility.get(field) or []
    if not isinstance(raw, list) or any(not isinstance(item, str) for item in raw):
        raise SurfaceError(f"assets_visibility.{field} must be a string list")
    return set(raw)


def infer_grader_assets(card: dict[str, Any]) -> tuple[str, ...]:
    """Infer public grader files solely from the canonical grading command."""
    card_id = card.get("id")
    if not isinstance(card_id, str) or not _SAFE_ID.fullmatch(card_id):
        raise SurfaceError("card id is unsafe")
    try:
        command = card["success_criteria"]["spec"]["command"]
    except (KeyError, TypeError) as exc:
        raise SurfaceError("card has no grading command") from exc
    if not isinstance(command, str):
        raise SurfaceError("grading command is not a string")

    found: set[str] = set()
    for match in _ASSET_REF.finditer(command):
        reference = match.group("path").rstrip(".,;:)")
        parts = PurePosixPath(reference).parts
        if not parts or parts[-1] not in GRADER_BASENAMES:
            continue
        # Corpus commands use assets/<card-id>/<relative-path>. Examples may
        # use assets/<relative-path>; accepting both keeps the SSOT reusable.
        rel_parts = parts[1:] if parts[0] == card_id else parts
        found.add(_safe_rel(PurePosixPath(*rel_parts).as_posix()))
    return tuple(sorted(found))


def validate_grader_authority(
    card: dict[str, Any], *, require_explicit: bool = False
) -> tuple[str, ...]:
    """Validate the explicit field, or return the inferred legacy authority."""
    inferred = infer_grader_assets(card)
    visibility = card.get("assets_visibility") or {}
    if not isinstance(visibility, dict):
        raise SurfaceError("assets_visibility must be an object")
    if "grader_sealed" not in visibility:
        if require_explicit and inferred:
            raise SurfaceError("assets_visibility.grader_sealed is required")
        declared = set(inferred)
    else:
        raw = visibility["grader_sealed"]
        if not isinstance(raw, list) or any(not isinstance(item, str) for item in raw):
            raise SurfaceError("assets_visibility.grader_sealed must be a string list")
        if len(raw) != len(set(raw)):
            raise SurfaceError("assets_visibility.grader_sealed contains duplicates")
        declared = {_safe_rel(item) for item in raw}
        if declared != set(inferred):
            raise SurfaceError("declared grader authority differs from command surface")

    hidden = _string_set(visibility, "sealed")
    editable = _string_set(visibility, "editable")
    if declared & hidden:
        raise SurfaceError("grader_sealed overlaps hidden sealed assets")
    if declared & editable:
        raise SurfaceError("grader_sealed overlaps editable assets")
    return tuple(sorted(declared))


def asset_root_for_card(
    card_path: str | Path, card_id: str, repo_root: str | Path | None = None
) -> Path:
    """Return the trusted asset directory for a corpus card or example card."""
    path = Path(card_path)
    if repo_root is not None:
        return Path(repo_root) / "cards" / "assets" / card_id
    try:
        if path.resolve().parent == (ROOT / "cards").resolve():
            return ROOT / "cards" / "assets" / card_id
    except OSError as exc:
        raise SurfaceError("card location is unavailable") from exc
    example_assets = path.parent / "assets"
    nested = example_assets / card_id
    return nested if nested.is_dir() else example_assets


def _open_dir(path: str | Path) -> int:
    if not _NOFOLLOW or not _DIRECTORY:
        raise SurfaceError("platform lacks symlink-safe open flags")
    try:
        return os.open(os.fspath(path), os.O_RDONLY | _DIRECTORY | _NOFOLLOW | _CLOEXEC)
    except OSError as exc:
        raise SurfaceError("safe directory open failed") from exc


def _walk_dirfd(root_fd: int, parts: Iterable[str], *, create: bool) -> int:
    current = os.dup(root_fd)
    try:
        for part in parts:
            try:
                child = os.open(
                    part, os.O_RDONLY | _DIRECTORY | _NOFOLLOW | _CLOEXEC,
                    dir_fd=current,
                )
            except FileNotFoundError:
                if not create:
                    raise SurfaceError("required directory is missing")
                try:
                    os.mkdir(part, 0o755, dir_fd=current)
                    child = os.open(
                        part, os.O_RDONLY | _DIRECTORY | _NOFOLLOW | _CLOEXEC,
                        dir_fd=current,
                    )
                except OSError as exc:
                    raise SurfaceError("safe directory creation failed") from exc
            except OSError as exc:
                raise SurfaceError("unsafe directory in grader path") from exc
            os.close(current)
            current = child
        return current
    except Exception:
        os.close(current)
        raise


def read_canonical_assets(asset_root: str | Path, relpaths: Iterable[str]) -> tuple[CanonicalAsset, ...]:
    """Read bounded, regular, singly-linked assets without following links."""
    root_fd = _open_dir(asset_root)
    assets: list[CanonicalAsset] = []
    try:
        for raw_rel in relpaths:
            rel = _safe_rel(raw_rel)
            parts = PurePosixPath(rel).parts
            parent_fd = _walk_dirfd(root_fd, parts[:-1], create=False)
            try:
                try:
                    fd = os.open(
                        parts[-1],
                        os.O_RDONLY | os.O_NONBLOCK | _NOFOLLOW | _CLOEXEC,
                        dir_fd=parent_fd,
                    )
                except OSError as exc:
                    raise SurfaceError("canonical grader asset cannot be opened safely") from exc
                try:
                    before = os.fstat(fd)
                    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                        raise SurfaceError("canonical grader asset is not a private regular file")
                    if before.st_size > MAX_GRADER_BYTES:
                        raise SurfaceError("canonical grader asset exceeds size limit")
                    chunks: list[bytes] = []
                    remaining = MAX_GRADER_BYTES + 1
                    while remaining:
                        chunk = os.read(fd, min(65536, remaining))
                        if not chunk:
                            break
                        chunks.append(chunk)
                        remaining -= len(chunk)
                    data = b"".join(chunks)
                    after = os.fstat(fd)
                    if len(data) > MAX_GRADER_BYTES or (
                        before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns
                    ) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
                        raise SurfaceError("canonical grader asset changed while reading")
                    mode = stat.S_IMODE(before.st_mode) & 0o555
                    if not mode & 0o444:
                        mode |= 0o444
                    assets.append(CanonicalAsset(rel, data, hashlib.sha256(data).hexdigest(), mode))
                finally:
                    os.close(fd)
            finally:
                os.close(parent_fd)
    finally:
        os.close(root_fd)
    return tuple(assets)


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise SurfaceError("short write while restoring grader")
        view = view[written:]


def restore_assets(workspace: str | Path, card_id: str,
                   assets: Iterable[CanonicalAsset]) -> None:
    """Atomically replace workspace graders without following destination links."""
    if not _SAFE_ID.fullmatch(card_id):
        raise SurfaceError("card id is unsafe")
    root_fd = _open_dir(workspace)
    try:
        for asset in assets:
            parts = ("assets", card_id, *PurePosixPath(_safe_rel(asset.relpath)).parts)
            parent_fd = _walk_dirfd(root_fd, parts[:-1], create=True)
            tmp_name = f".grader-restore-{secrets.token_hex(12)}"
            fd = -1
            try:
                fd = os.open(
                    tmp_name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | _NOFOLLOW | _CLOEXEC,
                    asset.mode,
                    dir_fd=parent_fd,
                )
                _write_all(fd, asset.data)
                os.fchmod(fd, asset.mode)
                os.fsync(fd)
                os.close(fd)
                fd = -1
                os.replace(tmp_name, parts[-1], src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
                os.fsync(parent_fd)
            except OSError as exc:
                raise SurfaceError("atomic grader restore failed") from exc
            finally:
                if fd >= 0:
                    os.close(fd)
                try:
                    os.unlink(tmp_name, dir_fd=parent_fd)
                except FileNotFoundError:
                    pass
                except OSError:
                    pass
                os.close(parent_fd)
    finally:
        os.close(root_fd)


def verify_assets(workspace: str | Path, card_id: str,
                  assets: Iterable[CanonicalAsset]) -> None:
    """Verify restored content, link count, type, and read-only mode."""
    root_fd = _open_dir(workspace)
    try:
        for asset in assets:
            parts = ("assets", card_id, *PurePosixPath(_safe_rel(asset.relpath)).parts)
            parent_fd = _walk_dirfd(root_fd, parts[:-1], create=False)
            try:
                try:
                    fd = os.open(
                        parts[-1], os.O_RDONLY | os.O_NONBLOCK | _NOFOLLOW | _CLOEXEC,
                        dir_fd=parent_fd,
                    )
                except OSError as exc:
                    raise SurfaceError("restored grader cannot be opened safely") from exc
                try:
                    info = os.fstat(fd)
                    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                            or stat.S_IMODE(info.st_mode) & 0o222
                            or info.st_size > MAX_GRADER_BYTES):
                        raise SurfaceError("restored grader metadata is unsafe")
                    digest = hashlib.sha256()
                    total = 0
                    while True:
                        chunk = os.read(fd, 65536)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_GRADER_BYTES:
                            raise SurfaceError("restored grader exceeds size limit")
                        digest.update(chunk)
                    if digest.hexdigest() != asset.sha256:
                        raise SurfaceError("restored grader hash mismatch")
                finally:
                    os.close(fd)
            finally:
                os.close(parent_fd)
    finally:
        os.close(root_fd)


def prepare_grader_assets(card: dict[str, Any], card_path: str | Path,
                          workspace: str | Path, *, repo_root: str | Path | None = None
                          ) -> tuple[CanonicalAsset, ...]:
    relpaths = validate_grader_authority(card)
    if not relpaths:
        return ()
    asset_root = asset_root_for_card(card_path, str(card["id"]), repo_root)
    assets = read_canonical_assets(asset_root, relpaths)
    restore_assets(workspace, str(card["id"]), assets)
    verify_assets(workspace, str(card["id"]), assets)
    return assets


def corpus_census(repo_root: str | Path = ROOT, *, require_explicit: bool = False
                  ) -> dict[str, int]:
    root = Path(repo_root)
    cards = sorted((root / "cards").glob("gc-*.json"))
    surface = grade_or_check = self_report = 0
    for path in cards:
        card = json.loads(path.read_text(encoding="utf-8"))
        relpaths = validate_grader_authority(card, require_explicit=require_explicit)
        if relpaths:
            read_canonical_assets(
                root / "cards" / "assets" / str(card["id"]), relpaths
            )
            surface += 1
        if any(PurePosixPath(rel).name in {"grade.py", "check.sh"} for rel in relpaths):
            grade_or_check += 1
        command = card.get("success_criteria", {}).get("spec", {}).get("command", "")
        if not relpaths and isinstance(command, str) and "score.json" in command:
            self_report += 1
    return {"cards": len(cards), "grader_surface": surface,
            "grade_or_check": grade_or_check, "self_report": self_report}


def check_corpus(repo_root: str | Path = ROOT, *, require_explicit: bool = False
                 ) -> dict[str, int]:
    counts = corpus_census(repo_root, require_explicit=require_explicit)
    if counts != EXPECTED_CENSUS:
        raise SurfaceError("grading-surface census mismatch")
    return counts


def sync_cards(repo_root: str | Path = ROOT, *, apply: bool = False) -> int:
    """Synchronize explicit authority fields; dry-run unless ``apply`` is true."""
    changed = 0
    for path in sorted((Path(repo_root) / "cards").glob("gc-*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))
        inferred = list(infer_grader_assets(card))
        visibility = card.get("assets_visibility")
        current = visibility.get("grader_sealed") if isinstance(visibility, dict) else None
        if current == inferred or (not inferred and current is None):
            continue
        changed += 1
        if not apply:
            continue
        if visibility is None:
            visibility = {}
            card["assets_visibility"] = visibility
        if not isinstance(visibility, dict):
            raise SurfaceError("assets_visibility must be an object")
        if inferred:
            visibility["grader_sealed"] = inferred
        else:
            visibility.pop("grader_sealed", None)
            if not visibility:
                card.pop("assets_visibility", None)
        validate_grader_authority(card, require_explicit=bool(inferred))
        payload = (json.dumps(card, ensure_ascii=False, indent=1) + "\n").encode()
        tmp = path.with_name(f".{path.name}.sync-{secrets.token_hex(8)}")
        try:
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | _NOFOLLOW, 0o600)
            try:
                _write_all(fd, payload)
                os.fsync(fd)
            finally:
                os.close(fd)
            os.chmod(tmp, stat.S_IMODE(path.stat().st_mode))
            os.replace(tmp, path)
        finally:
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("--require-explicit", action="store_true")
    sync = sub.add_parser("sync")
    sync.add_argument("--apply", action="store_true",
                      help="write card JSON (default: report a dry run)")
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            counts = check_corpus(require_explicit=args.require_explicit)
            print(json.dumps({"ok": True, **counts}, sort_keys=True))
        else:
            changed = sync_cards(apply=args.apply)
            print(json.dumps({"applied": bool(args.apply), "cards_changed": changed},
                             sort_keys=True))
        return 0
    except (OSError, ValueError, json.JSONDecodeError, SurfaceError):
        print(json.dumps({"ok": False, "error": "grading surface invalid"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
