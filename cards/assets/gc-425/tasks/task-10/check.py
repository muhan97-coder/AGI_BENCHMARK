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
ok_content = raw == b"hello benchmark"
ok_hash = hashlib.sha256(raw).hexdigest() == "c8ab33c47610a76e3d6d2d03d33e81f006c3ad90a5217ea72ef049c8bf973481"
result(ok_content and ok_hash)
