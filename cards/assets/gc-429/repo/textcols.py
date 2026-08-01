"""Greedy text wrapping and column layout helpers (gc-429 target)."""
from __future__ import annotations


def wrap(text: str, width: int) -> list[str]:
    """Greedy word wrap; words longer than width go on their own line."""
    if width < 1:
        raise ValueError("width must be >= 1")
    lines: list[str] = []
    cur = ""
    for word in text.split():
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= width:
            cur = cur + " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def pad(line: str, width: int, align: str = "left") -> str:
    """Pad with spaces to width; align is left, right or center."""
    gap = width - len(line)
    if gap <= 0:
        return line
    if align == "left":
        return line + " " * gap
    if align == "right":
        return " " * gap + line
    if align == "center":
        left = gap // 2
        return " " * left + line + " " * (gap - left)
    raise ValueError("unknown align")


def columns(items: list[str], width: int, gutter: int = 2) -> list[str]:
    """Lay items into as many equal columns as fit; column-major order."""
    if not items:
        return []
    cell = max(len(s) for s in items)
    ncols = max(1, (width + gutter) // (cell + gutter))
    nrows = -(-len(items) // ncols)
    out = []
    for r in range(nrows):
        row = []
        for c in range(ncols):
            k = c * nrows + r
            if k < len(items):
                row.append(pad(items[k], cell))
        out.append((" " * gutter).join(row).rstrip())
    return out


def truncate(line: str, width: int, ellipsis: str = "...") -> str:
    """Cut to width, appending ellipsis when cut; width >= len(ellipsis)."""
    if width < len(ellipsis):
        raise ValueError("width too small for ellipsis")
    if len(line) <= width:
        return line
    return line[:width - len(ellipsis)] + ellipsis
