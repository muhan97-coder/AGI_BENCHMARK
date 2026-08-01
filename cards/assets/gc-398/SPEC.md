# semverx — Semantic Versioning 2.0.0 library (spec v1)

Implement a pure-Python module at `workspace/gc-398/semverx.py` (relative to
the benchmark repo root). No third-party imports. Public API:

## `is_valid(s: str) -> bool`
True iff `s` is a valid SemVer 2.0.0 version string (semver.org). Summary:
`MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]` where
- MAJOR/MINOR/PATCH: non-negative integers, **no leading zeros** (`0` is fine,
  `01` is not).
- PRERELEASE: dot-separated identifiers, each non-empty, chars `[0-9A-Za-z-]`.
  Purely numeric identifiers must have **no leading zeros**.
- BUILD: dot-separated identifiers, each non-empty, chars `[0-9A-Za-z-]`.
  Leading zeros are allowed here.
- No `v` prefix, no whitespace.

## `parse(s: str) -> dict`
Returns `{"major": int, "minor": int, "patch": int, "prerelease": list,
"build": list}`. Prerelease identifiers that are purely numeric become `int`,
others stay `str`. Build identifiers always stay `str`. Raises `ValueError`
on invalid input.

## `compare(a: str, b: str) -> int`
Returns -1, 0, or 1 by SemVer **precedence** (build metadata ignored):
1. Compare major, minor, patch numerically.
2. A version with a prerelease has LOWER precedence than the same version
   without one.
3. Prerelease lists compare identifier by identifier:
   - numeric vs numeric: numerically
   - alphanumeric vs alphanumeric: ASCII string order
   - numeric identifiers ALWAYS have lower precedence than alphanumeric ones
   - if all shared identifiers are equal, the longer list wins.
Raises `ValueError` if either input is invalid.

## `max_version(versions: list[str]) -> str`
Returns the input string with the highest precedence. If several inputs tie on
precedence (e.g. differ only in build metadata), return the EARLIEST of the
tied ones in list order. Raises `ValueError` on an empty list or if any
element is invalid.

## Edge cases (deliberately tricky — read carefully)
- `1.0.0-alpha` < `1.0.0-alpha.1` < `1.0.0-alpha.beta` < `1.0.0-beta`
  < `1.0.0-beta.2` < `1.0.0-beta.11` < `1.0.0-rc.1` < `1.0.0`
- `1.0.0-1` is valid (numeric prerelease); `1.0.0-01` is INVALID.
- `1.0.0-alpha.01` is INVALID, but `1.0.0-alpha.0a1` is valid
  (leading zero allowed when the identifier is not purely numeric).
- `1.0.0+001` and `1.0.0+exp.sha.5114f85` are valid; build never affects
  precedence: `compare("1.0.0+a", "1.0.0+b") == 0`.
- `1.0.0-alpha-1` is valid: `alpha-1` is one alphanumeric identifier.
- `01.0.0`, `1.00.0`, `1.0`, `1.0.0.0`, `1.0.0-`, `1.0.0-alpha..1`,
  `v1.0.0`, ` 1.0.0` are all INVALID.
- `compare("1.0.0-2", "1.0.0-11")` is -1 (numeric, not lexicographic).

## Acceptance
Sealed suite: `assets/gc-398/test_accept.py`, run from the repo root with
pytest. Do not modify the test file.
