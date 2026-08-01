"""logfmt: minimal logfmt line parsing (sealed).

Grammar per line: space-separated pairs. A pair is `key`, `key=`,
`key=bare-value`, or `key="quoted value"` with `\"` and `\\` escapes.
A bare key (no `=`) has value True; `key=` has value "". Keys match
[A-Za-z_][A-Za-z0-9_]*; duplicates: last one wins. Malformed input
raises ValueError. An empty line parses to {}.
"""
import re

_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def parse_line(line):
    result = {}
    i = 0
    n = len(line)
    while i < n:
        if line[i] == " ":
            i += 1
            continue
        m = _KEY.match(line, i)
        if not m:
            raise ValueError(f"bad key at {i}")
        key = m.group(0)
        i = m.end()
        if i >= n or line[i] == " ":
            result[key] = True
            continue
        if line[i] != "=":
            raise ValueError(f"expected '=' at {i}")
        i += 1
        if i < n and line[i] == '"':
            i += 1
            buf = []
            while True:
                if i >= n:
                    raise ValueError("unterminated quote")
                c = line[i]
                if c == "\\":
                    if i + 1 >= n:
                        raise ValueError("unterminated quote")
                    nxt = line[i + 1]
                    if nxt not in ('"',):
                        raise ValueError(f"bad escape at {i}")
                    buf.append(nxt)
                    i += 2
                elif c == '"':
                    i += 1
                    break
                else:
                    buf.append(c)
                    i += 1
            result[key] = "".join(buf)
        else:
            j = line.find(" ", i)
            if j == -1:
                j = n
            result[key] = line[i:j]
            i = j
    return result
