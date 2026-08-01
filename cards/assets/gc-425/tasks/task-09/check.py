#!/usr/bin/env python3
"""Sealed checker. Usage: python3 check.py <output_file>. Prints {"ok": bool}."""
import hashlib, json, sys
from pathlib import Path
HERE = Path(__file__).parent
def result(ok):
    print(json.dumps({"ok": bool(ok)}))
    sys.exit(0)
try:
    raw = Path(sys.argv[1]).read_bytes()
    text = raw.decode("utf-8")
except Exception:
    result(False)
rows = [r.split(",") for r in (HERE/"input.txt").read_text().strip().splitlines()]
want = "\n".join(",".join(col) for col in zip(*rows))
result(text.strip() == want)
