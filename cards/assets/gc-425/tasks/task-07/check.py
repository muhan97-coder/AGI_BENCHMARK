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
want = hashlib.sha256((HERE/"input.txt").read_bytes()).hexdigest()
result(text.strip() == want)
