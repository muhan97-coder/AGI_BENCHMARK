# gc-333 Interface Contract — MultiAgentMaze (MARBLE coding task_id=17)

Source task: MARBLE repo `multiagentbench/coding/coding_main.jsonl`, task_id=17, at
commit `8892e9cfb69282db568e6b018f2b1cd8eec31ba6`.

Implement `workspace/gc-333/solution.py`. The module must define
`IllegalMove(Exception)` and `MazeGame`.

Grid cells: `#` wall, `.` floor, `S` start (floor), `E` exit, `B` movable block.
Positions are `(row, col)` tuples; directions are `"up" | "down" | "left" | "right"`.

## class MazeGame(levels: list[list[str]])

- `levels` is a non-empty list of grids; each grid is a list of equal-length strings.
  Raise `ValueError` for: any other character, a grid without exactly one `S`, a grid
  without exactly one `E`, or ragged rows.
- Play starts on level 0 with the avatar on that level's `S`. When a level loads, the
  engine records `opt` = shortest-path length from `S` to `E` at load time (blocks
  count as obstacles; may be `None` if unreachable).
- `add_player(name, role)` — role in `{"pathfinder","blocker","swapper"}` else
  `ValueError`; duplicate name raises `ValueError`.
- `move(player, direction)` — pathfinder only, otherwise `PermissionError`. Moves the
  avatar one cell. Off-grid, wall, or block target raises `IllegalMove`. Floor (`.`,
  `S`) and `E` are enterable.
- `push(player, block_pos, direction)` — blocker only (`PermissionError`). There must
  be a block at `block_pos` and the destination cell must be inside the grid, floor
  (`.` or `S`), and not the avatar's cell, else `IllegalMove`.
- `swap(player, pos1, pos2)` — swapper only (`PermissionError`). Exactly one position
  holds a block and the other is floor (`.` or `S`); neither may be a wall, `E`, or
  the avatar's cell, else `IllegalMove`. Teleports the block.
- Every successful `move`/`push`/`swap` increments the current level's action counter
  `moves`. Failed attempts do not.
- `hint() -> int | None` — BFS shortest-path length (steps) from the avatar to `E`
  through non-wall, non-block cells, `None` if unreachable.
- Completing a level (avatar enters `E`): add to score
  `max(0, 1000 - 10 * moves)` plus a teamwork bonus of `50` if `opt` is not `None`
  and `moves <= opt + 2`. Then, if a next level exists, load it (avatar at its `S`,
  `moves` reset to 0); otherwise `finished` becomes `True`.
- `state() -> dict` — keys `"level"` (0-based index), `"avatar"` (tuple),
  `"blocks"` (sorted list of positions), `"moves"` (this level), `"score"` (total),
  `"finished"` (bool).
