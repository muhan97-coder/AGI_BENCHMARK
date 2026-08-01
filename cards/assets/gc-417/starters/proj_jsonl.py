"""proj_jsonl: JSON-lines utilities (gc-417 starter; seeded defects)."""
import json


def parse_lines(text):
    out = []
    for line in text.splitlines():
        out.append(json.loads(line))
    return out


def filter_records(records, key, value):
    return [r for r in records if r[key] == value]


def summarize(records, key):
    missing = sum(1 for r in records if not r.get(key))
    present = [r[key] for r in records if r.get(key)]
    return {"count": len(records), "missing": missing,
            "distinct": len(set(present))}
