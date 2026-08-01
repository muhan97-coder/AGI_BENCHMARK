"""Minimal CSV parse/serialize with quoting (mutation target for gc-428)."""
from __future__ import annotations


def split_line(line: str) -> list[str]:
    """Split one CSV line honoring double-quote quoting and "" escapes."""
    fields: list[str] = []
    buf: list[str] = []
    in_quotes = False
    i = 0
    while i < len(line):
        ch = line[i]
        if in_quotes:
            if ch == '"':
                if i + 1 < len(line) and line[i + 1] == '"':
                    buf.append('"')
                    i += 1
                else:
                    in_quotes = False
            else:
                buf.append(ch)
        else:
            if ch == '"':
                in_quotes = True
            elif ch == ',':
                fields.append(''.join(buf))
                buf = []
            else:
                buf.append(ch)
        i += 1
    if in_quotes:
        raise ValueError("unterminated quote")
    fields.append(''.join(buf))
    return fields


def needs_quoting(field: str) -> bool:
    return any(ch in field for ch in (',', '"', '\n'))


def format_field(field: str) -> str:
    if needs_quoting(field):
        return '"' + field.replace('"', '""') + '"'
    return field


def format_line(fields: list[str]) -> str:
    return ','.join(format_field(f) for f in fields)


def parse(text: str) -> list[list[str]]:
    """Parse newline-separated CSV text (no embedded newlines in fields)."""
    rows = []
    for line in text.splitlines():
        rows.append(split_line(line))
    return rows


def serialize(rows: list[list[str]]) -> str:
    return '\n'.join(format_line(r) for r in rows)


def column(rows: list[list[str]], idx: int) -> list[str]:
    """Values of column idx; short rows contribute an empty string."""
    out = []
    for r in rows:
        if idx < len(r):
            out.append(r[idx])
        else:
            out.append('')
    return out
