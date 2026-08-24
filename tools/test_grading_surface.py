#!/usr/bin/env python3
"""Focused stdlib tests for public grader sealing."""
from __future__ import annotations

import copy
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

try:
    from assemble_workspace import assemble
    from goal_grader import grade
    from grading_surface import (
        EXPECTED_CENSUS,
        ROOT,
        SurfaceError,
        check_corpus,
        infer_grader_assets,
        read_canonical_assets,
        sync_cards,
        validate_grader_authority,
    )
except ModuleNotFoundError:
    from tools.assemble_workspace import assemble
    from tools.goal_grader import grade
    from tools.grading_surface import (
        EXPECTED_CENSUS,
        ROOT,
        SurfaceError,
        check_corpus,
        infer_grader_assets,
        read_canonical_assets,
        sync_cards,
        validate_grader_authority,
    )


def _ids(start: int, end: int) -> set[str]:
    return {f"gc-{number:03d}" for number in range(start, end + 1)}


class SurfacePolicyTests(unittest.TestCase):
    def _card(self, command: str) -> dict[str, object]:
        return {
            "id": "t-001",
            "success_criteria": {
                "grader": "script",
                "spec": {
                    "command": command,
                    "metric": "score",
                    "threshold": 1,
                    "compare": ">=",
                },
            },
        }

    def test_command_surface_infers_all_three_canonical_programs(self) -> None:
        cases = {
            "python3 assets/t-001/grade.py": ("grade.py",),
            "bash assets/t-001/check.sh": ("check.sh",),
            "python -m pytest assets/t-001/test_accept.py -q": ("test_accept.py",),
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                self.assertEqual(infer_grader_assets(self._card(command)), expected)

    def test_explicit_authority_is_exact_and_separate_from_hidden_assets(self) -> None:
        card = self._card("python3 assets/t-001/grade.py")
        self.assertEqual(validate_grader_authority(card), ("grade.py",))
        with self.assertRaises(SurfaceError):
            validate_grader_authority(card, require_explicit=True)

        explicit = copy.deepcopy(card)
        explicit["assets_visibility"] = {"grader_sealed": ["grade.py"]}
        self.assertEqual(validate_grader_authority(explicit), ("grade.py",))
        for bad in (
            {"grader_sealed": ["../grade.py"]},
            {"grader_sealed": ["check.sh"]},
            {"grader_sealed": ["grade.py"], "sealed": ["grade.py"]},
            {"grader_sealed": ["grade.py"], "editable": ["grade.py"]},
        ):
            broken = copy.deepcopy(card)
            broken["assets_visibility"] = bad
            with self.subTest(visibility=bad), self.assertRaises(SurfaceError):
                validate_grader_authority(broken)

    def test_public_corpus_census_and_exact_card_sets(self) -> None:
        self.assertEqual(check_corpus(ROOT), EXPECTED_CENSUS)
        actual: dict[str, tuple[str, ...]] = {}
        for path in (ROOT / "cards").glob("gc-*.json"):
            card = json.loads(path.read_text(encoding="utf-8"))
            relpaths = validate_grader_authority(card)
            if relpaths:
                actual[str(card["id"])] = relpaths
        grade_or_check = (
            _ids(312, 323) | _ids(348, 359) | _ids(372, 395)
            | _ids(408, 431) | _ids(440, 451) | _ids(464, 475)
        )
        test_accept = _ids(324, 335) | _ids(396, 407)
        self.assertEqual(set(actual), grade_or_check | test_accept)
        self.assertEqual(
            {cid for cid, paths in actual.items() if "test_accept.py" in paths},
            test_accept,
        )
        mutation = {
            str(json.loads(path.read_text(encoding="utf-8"))["id"])
            for path in (ROOT / "cards").glob("gc-*.json")
            if json.loads(path.read_text(encoding="utf-8"))
            .get("success_criteria", {}).get("grader") == "mutation"
        }
        self.assertEqual(mutation, _ids(348, 359) | {"gc-422", "gc-423", "gc-428", "gc-430"})
        self.assertTrue(mutation <= grade_or_check)

    def test_sync_is_dry_run_by_default_and_apply_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            cards = repo / "cards"
            cards.mkdir()
            path = cards / "gc-001_fixture.json"
            card = self._card("python3 assets/t-001/grade.py")
            path.write_text(json.dumps(card), encoding="utf-8")
            before = path.read_bytes()
            self.assertEqual(sync_cards(repo), 1)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(sync_cards(repo, apply=True), 1)
            synced = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(synced["assets_visibility"]["grader_sealed"], ["grade.py"])
            self.assertEqual(validate_grader_authority(synced, require_explicit=True),
                             ("grade.py",))


class GraderRestorationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.repo = base / "repo"
        self.workspace = base / "workspace"
        self.asset_dir = self.repo / "cards" / "assets" / "t-001"
        self.asset_dir.mkdir(parents=True)
        self.workspace.mkdir()
        self.card = {
            "id": "t-001",
            "success_criteria": {
                "grader": "script",
                "spec": {
                    "command": "python3 assets/t-001/grade.py",
                    "metric": "score",
                    "threshold": 1,
                    "compare": ">=",
                },
            },
        }
        self.card_path = self.repo / "cards" / "t-001.json"
        self.card_path.write_text(json.dumps(self.card), encoding="utf-8")
        self.canonical = self.asset_dir / "grade.py"
        self.canonical.write_text('import json\nprint(json.dumps({"score": 0}))\n',
                                  encoding="utf-8")
        self.dest_dir = self.workspace / "assets" / "t-001"
        self.dest_dir.mkdir(parents=True)
        self.dest = self.dest_dir / "grade.py"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _run(self) -> dict[str, object]:
        return grade(self.card_path, self.workspace, timeout_s=10,
                     repo_root=self.repo)

    def test_candidate_stub_is_replaced_before_grade(self) -> None:
        self.dest.write_text('print("{\\"score\\": 1}")\n', encoding="utf-8")
        result = self._run()
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["metric_value"], 0.0)
        self.assertEqual(self.dest.read_bytes(), self.canonical.read_bytes())
        self.assertFalse(stat.S_IMODE(self.dest.stat().st_mode) & 0o222)

    def test_destination_symlink_is_atomically_replaced(self) -> None:
        outside = Path(self.temp.name) / "outside.py"
        outside.write_text("sentinel\n", encoding="utf-8")
        self.dest.symlink_to(outside)
        result = self._run()
        self.assertEqual(result["verdict"], "FAIL")
        self.assertFalse(self.dest.is_symlink())
        self.assertEqual(outside.read_text(encoding="utf-8"), "sentinel\n")

    def test_destination_hardlink_is_broken_without_touching_peer(self) -> None:
        outside = Path(self.temp.name) / "outside.py"
        outside.write_text("sentinel\n", encoding="utf-8")
        os.link(outside, self.dest)
        result = self._run()
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(outside.read_text(encoding="utf-8"), "sentinel\n")
        self.assertEqual(self.dest.stat().st_nlink, 1)

    def test_destination_fifo_is_replaced_without_blocking(self) -> None:
        os.mkfifo(self.dest)
        result = self._run()
        self.assertEqual(result["verdict"], "FAIL")
        self.assertTrue(stat.S_ISREG(os.lstat(self.dest).st_mode))

    def test_parent_symlink_fails_closed_without_escape(self) -> None:
        self.dest_dir.rmdir()
        (self.workspace / "assets").rmdir()
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (self.workspace / "assets").symlink_to(outside, target_is_directory=True)
        result = self._run()
        self.assertEqual(result["verdict"], "GRADER_INVALID")
        self.assertFalse((outside / "t-001" / "grade.py").exists())

    def test_post_run_mutation_is_detected_fail_closed(self) -> None:
        self.canonical.write_text(
            "import json, os\n"
            "from pathlib import Path\n"
            "p=Path(__file__)\n"
            "os.chmod(p, 0o644)\n"
            "p.write_text('changed')\n"
            "print(json.dumps({'score': 1}))\n",
            encoding="utf-8",
        )
        result = self._run()
        self.assertEqual(result["verdict"], "GRADER_TAMPERED")
        self.assertFalse(result["passed"])

    def test_canonical_sources_reject_symlink_hardlink_and_fifo(self) -> None:
        root = Path(self.temp.name) / "source-types"
        root.mkdir()
        outside = Path(self.temp.name) / "peer"
        outside.write_text("x", encoding="utf-8")
        attacks = ("symlink", "hardlink", "fifo")
        for attack in attacks:
            target = root / "grade.py"
            if target.exists() or target.is_symlink():
                target.unlink()
            if attack == "symlink":
                target.symlink_to(outside)
            elif attack == "hardlink":
                os.link(outside, target)
            else:
                os.mkfifo(target)
            with self.subTest(attack=attack), self.assertRaises(SurfaceError):
                read_canonical_assets(root, ["grade.py"])

    def test_assembler_hides_oracles_but_exposes_read_only_grader(self) -> None:
        self.card["assets_visibility"] = {"sealed": ["answer.txt"]}
        self.card_path.write_text(json.dumps(self.card), encoding="utf-8")
        (self.asset_dir / "README.txt").write_text("task\n", encoding="utf-8")
        (self.asset_dir / "answer.txt").write_text("hidden\n", encoding="utf-8")
        (self.asset_dir / "answer.txt.sha256").write_text("commitment\n", encoding="utf-8")
        assembled = Path(self.temp.name) / "assembled"
        result = assemble(self.card_path, assembled, repo_root=self.repo)
        out = assembled / "assets" / "t-001"
        self.assertEqual(result["grader_sealed"], 1)
        self.assertTrue((out / "README.txt").is_file())
        self.assertFalse((out / "answer.txt").exists())
        self.assertFalse((out / "answer.txt.sha256").exists())
        self.assertFalse(stat.S_IMODE((out / "grade.py").stat().st_mode) & 0o222)


if __name__ == "__main__":
    unittest.main()
