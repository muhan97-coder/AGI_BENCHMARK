# taskgraph — deterministic dependency scheduler (spec v1)

Implement a pure-Python module at `workspace/gc-406/taskgraph.py` (relative
to the benchmark repo root). Standard library only.

## Input format
`tasks` is a dict: `{name: {"deps": [names...], "duration": int}}`.

Validation (applies to every API function, checked BEFORE cycle detection):
- Every dep name must be a key of `tasks`; unknown dep -> `ValueError`.
- Duplicate names inside one `deps` list are allowed and de-duplicated.
- `duration` must be an `int >= 1` (bool does NOT count as int here);
  anything else -> `ValueError`.
- An empty `tasks` dict is valid.

## Exceptions
Expose `class CycleError(Exception)` with an attribute `.cycle`: a list of
task names forming a dependency cycle, where `cycle[i]` DEPENDS ON
`cycle[(i+1) % len(cycle)]`. The list is normalized to start at its
lexicographically smallest member, and contains no repeated names.
If several distinct cycles exist, any one valid cycle is acceptable.

## API
### `order(tasks) -> list[str]`
Kahn's algorithm with a deterministic tie-break: among all currently
available tasks (all deps already emitted), always emit the
lexicographically smallest name first. Raises `CycleError` if no complete
ordering exists. A task depending on itself is a cycle of length 1.

### `waves(tasks) -> list[list[str]]`
Wave 0 = all tasks with no deps; wave k = all tasks whose deps all lie in
waves 0..k-1. Each wave sorted lexicographically. Raises `CycleError` on
cycles. Empty input -> `[]`.

### `critical_path(tasks) -> tuple[int, list[str]]`
The chain `t1 -> t2 -> ... -> tk` (each `t(i+1)` depends on `t(i)`;
the returned list is in EXECUTION order, dependencies first) maximizing
total duration `sum(duration(ti))`. Returns `(total, [names...])`.
Tie-break: among all maximum-total chains, return the lexicographically
smallest name list (compared as a sequence, element by element).
Empty input -> `(0, [])`. Raises `CycleError` on cycles.

## Worked example
    tasks = {
      "build":  {"deps": ["fetch"],           "duration": 4},
      "fetch":  {"deps": [],                  "duration": 2},
      "lint":   {"deps": ["fetch"],           "duration": 1},
      "test":   {"deps": ["build", "lint"],   "duration": 3},
      "pack":   {"deps": ["test"],            "duration": 1},
    }
    order(tasks)  == ["fetch", "build", "lint", "test", "pack"]
    waves(tasks)  == [["fetch"], ["build", "lint"], ["test"], ["pack"]]
    critical_path(tasks) == (10, ["fetch", "build", "test", "pack"])

## Acceptance
Sealed suite: `assets/gc-406/test_accept.py`, run from the repo root with
pytest. Do not modify the test file.
