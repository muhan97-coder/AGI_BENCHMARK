"""Glob-style path matcher: *, ?, ** segments (mutation target for gc-428)."""
from __future__ import annotations


def _match_segment(pattern: str, name: str) -> bool:
    """Match one path segment with * and ? wildcards (no slashes here)."""
    pi, ni = 0, 0
    star = -1
    star_ni = 0
    while ni < len(name):
        if pi < len(pattern) and pattern[pi] in ('?', name[ni]):
            pi += 1
            ni += 1
        elif pi < len(pattern) and pattern[pi] == '*':
            star = pi
            star_ni = ni
            pi += 1
        elif star != -1:
            pi = star + 1
            star_ni += 1
            ni = star_ni
        else:
            return False
    while pi < len(pattern) and pattern[pi] == '*':
        pi += 1
    return pi == len(pattern)


def match(pattern: str, path: str) -> bool:
    """Match a /-separated path; '**' matches zero or more whole segments."""
    return _match_parts(pattern.split('/'), path.split('/'))


def _match_parts(pats: list[str], names: list[str]) -> bool:
    if not pats:
        return not names
    head = pats[0]
    if head == '**':
        for skip in range(len(names) + 1):
            if _match_parts(pats[1:], names[skip:]):
                return True
        return False
    if not names:
        return False
    if not _match_segment(head, names[0]):
        return False
    return _match_parts(pats[1:], names[1:])


def filter_paths(pattern: str, paths: list[str]) -> list[str]:
    """Paths matching pattern, input order preserved."""
    return [p for p in paths if match(pattern, p)]


def common_prefix(paths: list[str]) -> str:
    """Longest common whole-segment prefix, '' when none."""
    if not paths:
        return ''
    split = [p.split('/') for p in paths]
    prefix: list[str] = []
    for parts in zip(*split):
        first = parts[0]
        if all(x == first for x in parts[1:]):
            prefix.append(first)
        else:
            break
    return '/'.join(prefix)
