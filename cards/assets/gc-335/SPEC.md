# gc-335 Interface Contract — MultiTrackRacers (MARBLE coding task_id=53)

Source task: MARBLE repo `multiagentbench/coding/coding_main.jsonl`, task_id=53, at
commit `8892e9cfb69282db568e6b018f2b1cd8eec31ba6`.

Implement `workspace/gc-335/solution.py` with `Track`, `Vehicle`, `race`, `League`.

## class Track(name)

- `add_segment(kind, length)` — kind in `{"straight","curve","jump","obstacle"}`
  else `ValueError`; `length <= 0` raises `ValueError`; after `finalize()` raises
  `RuntimeError`.
- `finalize()` — total length must be >= 10 else `ValueError` (track stays open).
- `.segments` — list of `(kind, length)` in order; `.length` — total; `.finalized`.

## class Vehicle(name, speed, acceleration, handling)

- Each attribute is an int >= 1; their sum must be <= 12, else `ValueError`.
- `upgrade(attr, points)` — attr must be one of `"speed"|"acceleration"|"handling"`
  else `ValueError`; `points < 1` raises `ValueError`; raising the sum above 12
  raises `ValueError` and changes nothing.
- `add_ability(a)` — `a` in `{"boost","shield"}` else `ValueError`; a vehicle holds
  at most one ability, second call raises `RuntimeError`. `.ability` is the ability
  or `None`.

## Segment time formulas (exact)

- straight: `length / speed`
- curve:    `length / (speed * (0.5 + handling / 20))`
- jump:     `length / speed + 3.0 / acceleration`
- obstacle: `length / speed + (0.0 if ability == "shield" else 5.0 / handling)`

Total race time = sum of segment times; if `ability == "boost"`, multiply the total
by 0.9.

## race(track, vehicles) -> list[dict]

- `track.finalized` must be True else `RuntimeError`; empty vehicle list raises
  `ValueError`.
- Returns one `{"name", "time"}` dict per vehicle with `time` rounded to 6 decimal
  places, sorted by time ascending, then name ascending.

## class League()

- `record(results)` — takes a `race(...)` result list; awards 3 points to the first
  entry, 2 to the second, 1 to the third (fewer entries: award what exists).
- `standings() -> list` — `(name, points)` sorted by points desc, then name asc.
  Vehicles seen in any recorded race appear even with 0 points.
- `share_track(agent, track)` / `shared_tracks() -> list` of `(agent, track_name)`
  in share order.
