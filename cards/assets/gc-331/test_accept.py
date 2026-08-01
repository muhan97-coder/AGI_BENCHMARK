"""Sealed acceptance suite for gc-331 (MARBLE coding task_id=87: DataFlowCoordinator).

Loads the agent's solution from workspace/gc-331/solution.py relative to the
benchmark repo root. Graders run the pinned copy of this file; do not modify it.
"""
import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SOLUTION = _ROOT / "workspace" / "gc-331" / "solution.py"


def _load():
    spec = importlib.util.spec_from_file_location("solution_gc331", _SOLUTION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CSV = "\n".join([
    "id,name,qty,price",
    "1,apple,3,0.5",
    "2,banana,x,0.25",   # qty type error
    "3,,2,0.75",         # name missing
    "4,dates,4,1.5",
    "4,dates,4,1.5",     # duplicate of row 3 (index 4)
])

SCHEMA = {"id": "int", "qty": "int", "price": "float", "name": "str"}
REQUIRED = ["id", "name"]


@pytest.fixture()
def dc():
    return _load().DataFlowCoordinator()


@pytest.fixture()
def validated(dc):
    dc.ingest_csv(CSV)
    dc.validate(SCHEMA, REQUIRED)
    return dc


def test_ingest_counts_rows(dc):
    assert dc.ingest_csv(CSV) == 5


def test_ingest_empty_rejected(dc):
    with pytest.raises(ValueError):
        dc.ingest_csv("")
    with pytest.raises(ValueError):
        dc.ingest_csv("id,name")


def test_validate_before_ingest(dc):
    with pytest.raises(RuntimeError):
        dc.validate(SCHEMA, REQUIRED)


def test_transform_before_validate(dc):
    dc.ingest_csv(CSV)
    with pytest.raises(RuntimeError):
        dc.rename("id", "key")
    with pytest.raises(RuntimeError):
        dc.drop_duplicates()


def test_export_before_transform(dc):
    dc.ingest_csv(CSV)
    dc.validate(SCHEMA, REQUIRED)
    with pytest.raises(RuntimeError):
        dc.export_rows()
    with pytest.raises(RuntimeError):
        dc.export_csv()


def test_validate_missing_required_column(dc):
    dc.ingest_csv("id,qty\n1,2")
    with pytest.raises(ValueError):
        dc.validate({"id": "int"}, ["id", "name"])


def test_validate_counts(validated):
    # rows 1 (qty=x) and 2 (name empty) are invalid
    dc2 = _load().DataFlowCoordinator()
    dc2.ingest_csv(CSV)
    assert dc2.validate(SCHEMA, REQUIRED) == {"valid": 3, "invalid": 2}


def test_error_identities(validated):
    assert [tuple(e) for e in validated.errors()] == [
        (1, "qty", "type"), (2, "name", "missing")]


def test_casts_applied(validated):
    validated.drop_duplicates()
    rows = validated.export_rows()
    assert rows[0]["id"] == 1 and rows[0]["qty"] == 3
    assert abs(rows[0]["price"] - 0.5) < 1e-12
    assert rows[0]["name"] == "apple"


def test_rename_and_unknown(validated):
    validated.rename("qty", "quantity")
    rows = validated.export_rows()
    assert "quantity" in rows[0] and "qty" not in rows[0]
    with pytest.raises(KeyError):
        validated.rename("ghost", "x")


def test_drop_column(validated):
    validated.drop_column("price")
    assert "price" not in validated.export_rows()[0]
    with pytest.raises(KeyError):
        validated.drop_column("ghost")


def test_drop_duplicates(validated):
    validated.drop_duplicates()
    rows = validated.export_rows()
    assert len(rows) == 2  # apple, dates (duplicate removed)


def test_merge_columns(validated):
    validated.merge("label", ["id", "name"], "-")
    rows = validated.export_rows()
    assert rows[0]["label"] == "1-apple"
    assert rows[0]["id"] == 1 and rows[0]["name"] == "apple"
    with pytest.raises(KeyError):
        validated.merge("bad", ["ghost"], "-")


def test_export_csv_exact(validated):
    validated.drop_duplicates()
    validated.drop_column("price")
    out = validated.export_csv()
    assert out == "id,name,qty\n1,apple,3\n4,dates,4"


def test_export_rows_are_copies(validated):
    validated.drop_duplicates()
    rows = validated.export_rows()
    rows[0]["id"] = 999
    assert validated.export_rows()[0]["id"] == 1


def test_stage_status_transitions(dc):
    st = dc.stage_status()
    assert st == {"ingested": False, "validated": False,
                  "transformed": False, "exported": False}
    dc.ingest_csv(CSV)
    assert dc.stage_status()["ingested"] is True
    dc.validate(SCHEMA, REQUIRED)
    assert dc.stage_status()["validated"] is True
    dc.drop_duplicates()
    assert dc.stage_status()["transformed"] is True
    dc.export_rows()
    assert dc.stage_status()["exported"] is True


def test_reingest_resets_flags(dc):
    dc.ingest_csv(CSV)
    dc.validate(SCHEMA, REQUIRED)
    dc.drop_duplicates()
    dc.export_rows()
    dc.ingest_csv("id,name\n7,fig")
    st = dc.stage_status()
    assert st["ingested"] is True
    assert st["validated"] is False and st["transformed"] is False
    assert st["exported"] is False
    with pytest.raises(RuntimeError):
        dc.drop_duplicates()
