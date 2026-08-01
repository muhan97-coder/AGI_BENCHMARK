# ex-minecraft_build — placement plan (written before the first block)

Read from `work/ex-minecraft_build/data/map.json` **after** `judger.py prepare`, never
from `blueprint.json` alone: only the map carries world coordinates, the chest position
and the arena terrain.

## Material manifest and chest withdrawal

Chest at world `(-4, -60, 0)`, stock is exact:

| item | needed | withdraw |
|---|---|---|
| stone_bricks | 6 | 6 |
| furnace | 1 | 1 |
| oak_log | 1 | 1 |

No spare of anything — one wasted placement is one permanent hole, so every `place`
must be aimed at a coordinate from `map.json`.

## Arena survey (the step a blueprint-only plan skips)

`map.json.arena_blocks` = `[{"pos": [0, -60, 1], "name": "dirt"}]`. That cell is also a
blueprint target (`stone_bricks`). A `place` onto an occupied cell is rejected, so the
tape must `break` the dirt first; breaking returns the dirt to inventory, which is why
`leftover_inventory` ends at `{"dirt": 1}` rather than empty.

## Build order

1. `withdraw` all three items (one trip to the chest, cheaper in wall time).
2. `break (0,-60,1)` — clear the obstruction.
3. Floor y=-60, in column order: `(0,0) (0,1) (1,0) (1,1) (2,0) (2,1)` — 6 × stone_bricks.
4. Directional layer y=-59: `furnace` at `(0,-59,0)` facing **W**, `oak_log` at
   `(2,-59,1)` axis **x**. Facing is scored separately as `view_hit_rate`; place the
   directional blocks last so a facing repair never has to unstack the floor.

## Verify loop

`judger.py run` → read `block_hit_rate` and the `mismatch:` lines on stderr, which name
coordinates (`expected X, observed Y`). Repair the tape at those coordinates only, re-run,
and keep every snapshot in `data/score.json`. Stop at `block_hit_rate == 1.0`.

## Ledger discipline

Append `data/action_log.json` as the phases actually happen (survey / withdraw / build);
`duration` must equal its own interval, because the judger recomputes it and refuses to
score a ledger that disagrees with itself. `efficiency` = matched blocks per active
minute, so padding the intervals lowers the score instead of raising it.
