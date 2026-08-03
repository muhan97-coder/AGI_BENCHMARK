#!/usr/bin/env python3
"""The corpus fingerprint must be stable **and** must move when the cards do.

A hash that never changes is not an identity, it is a constant. The second half
of this file is the negative control: perturb one byte of one card, one byte of
one asset, and the digest has to follow. Without that check a broken hasher looks
exactly like a stable corpus.

Offline, no network, no fixtures beyond a temp tree.

    python3 tools/test_corpus_fingerprint.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "corpus_fingerprint.py"


def _fp(root: Path) -> dict:
    """Run the tool against a copy of the repo rooted at *root*."""
    out = subprocess.run([sys.executable, str(root / "tools" / "corpus_fingerprint.py"),
                          "--json"], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def _clone() -> Path:
    """A minimal copy: cards + assets + the tool. Nothing else is hashed."""
    d = Path(tempfile.mkdtemp(prefix="corpusfp_"))
    shutil.copytree(ROOT / "cards", d / "cards")
    (d / "tools").mkdir()
    shutil.copy2(TOOL, d / "tools" / "corpus_fingerprint.py")
    return d


def main() -> int:
    fails = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  {'✅' if ok else '❌'} {name}" + (f"\n       {detail}" if detail and not ok else ""))
        if not ok:
            fails.append(name)

    base = _clone()
    a = _fp(base)
    b = _fp(base)
    check("같은 트리 → 같은 지문", a["corpus_sha256"] == b["corpus_sha256"])
    check("카드 수가 실물과 맞다",
          a["cards"] == len(list((base / "cards").glob("gc-*.json"))))

    # ── 포맷 변경은 내용 변경이 아니다 ────────────────────────────────────────
    t = _clone()
    f = sorted((t / "cards").glob("gc-*.json"))[0]
    card = json.loads(f.read_text())
    f.write_text(json.dumps(card, indent=7, sort_keys=False, ensure_ascii=False))
    check("재들여쓰기는 지문을 바꾸지 않는다 (canonical JSON)",
          _fp(t)["corpus_sha256"] == a["corpus_sha256"],
          f"{_fp(t)['corpus_sha256'][:16]} vs {a['corpus_sha256'][:16]}")

    # ── 부정 대조: 내용이 바뀌면 반드시 따라 움직인다 ────────────────────────
    t = _clone()
    f = sorted((t / "cards").glob("gc-*.json"))[0]
    card = json.loads(f.read_text())
    card["success_criteria"]["spec"]["threshold"] = 99999
    f.write_text(json.dumps(card, ensure_ascii=False))
    check("임계값 한 개 변경 → 지문이 바뀐다",
          _fp(t)["corpus_sha256"] != a["corpus_sha256"])

    t = _clone()
    assets = sorted((t / "cards" / "assets").glob("gc-*"))
    target = next((p for p in assets if any(x.is_file() for x in p.rglob("*"))), None)
    if target is None:
        check("자산 변경 → 지문이 바뀐다", False, "자산 있는 카드를 못 찾음")
    else:
        victim = next(x for x in sorted(target.rglob("*")) if x.is_file())
        victim.write_bytes(victim.read_bytes() + b"\n# perturbed\n")
        check(f"자산 1바이트 변경 → 지문이 바뀐다 ({target.name}/{victim.name})",
              _fp(t)["corpus_sha256"] != a["corpus_sha256"])

    t = _clone()
    sorted((t / "cards").glob("gc-*.json"))[0].unlink()
    ft = _fp(t)
    check("카드 삭제 → 지문·개수 둘 다 바뀐다",
          ft["corpus_sha256"] != a["corpus_sha256"] and ft["cards"] == a["cards"] - 1)

    # ── 카드별 해시가 실제로 그 카드만 가리키는가 ────────────────────────────
    t = _clone()
    files = sorted((t / "cards").glob("gc-*.json"))
    c0 = json.loads(files[0].read_text())
    c0["title"] = c0.get("title", "") + " (edited)"
    files[0].write_text(json.dumps(c0, ensure_ascii=False))
    per_before = {c["id"]: c["card_sha256"] for c in a["per_card"]}
    per_after = {c["id"]: c["card_sha256"] for c in _fp(t)["per_card"]}
    moved = [k for k in per_before if per_before[k] != per_after.get(k)]
    check("카드 하나를 고치면 그 카드의 해시만 움직인다",
          len(moved) == 1, f"움직인 카드: {moved}")

    print(f"\n  {len(fails) and '실패 ' + str(fails) or '전부 통과'}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
