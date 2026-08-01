# ex-minecraft_build Runbook (sealed — follow exactly; grading depends on these paths)

All paths are relative to the workspace root (the directory you point the
grader at). This is the miniature, docker-free stand-in for the MARBLE
`build_judger` runbook that ships with the scored minecraft_build cards
(cf. `cards/assets/gc-360/RUNBOOK.md`): same phases, same path contract, same
fail-closed ledger requirement — no Minecraft server, no Node, no docker.

## 1. Fresh arena (never assume a prepared one)

    python3 assets/ex-minecraft_build/judger.py prepare \
        --task ex-minecraft_build --idx 0 --agent_names builder_a

`prepare` shifts the sealed blueprint into world space, stocks the material
chest with the EXACT manifest, drops the pre-existing arena terrain, and writes

    work/ex-minecraft_build/data/map.json          world-space targets + chest + stock
    work/ex-minecraft_build/.cache/load_status.cache   {"status": "loaded"}

It also clears `data/score.json` (the snapshot feed) and deletes any earlier
`result/ex-minecraft_build/score.json`: a fresh arena invalidates old readings.
Re-running `prepare` is the equivalent of `docker compose down && up` on the
scored cards — it never touches your plan or your ledgers.

**Read `map.json` before planning.** The blueprint is blueprint-relative; only
`map.json` has the world coordinates, the chest position, and `arena_blocks` —
terrain that already occupies a cell you need. A plan written from
`blueprint.json` alone will land a block short.

## 2. Build (your deliverable)

Write the bot's action tape to

    work/ex-minecraft_build/data/build_plan.json

    {"bot": "builder_a",
     "actions": [
       {"t": "withdraw", "item": "stone_bricks", "count": 6},
       {"t": "break",    "pos": [0, -60, 1]},
       {"t": "place",    "pos": [0, -60, 0], "block": "stone_bricks"},
       {"t": "place",    "pos": [0, -59, 0], "block": "furnace", "facing": "W"}
     ]}

Verbs: `withdraw` (chest → inventory; the chest stock is exact, so an
over-withdrawal is logged as a plan error and a wasted placement leaves you
short), `place` (inventory → world; fails on an occupied cell), `break`
(world → inventory; the only way to clear `arena_blocks`).

## 3. Honest ledgers (REQUIRED — scoring is fail-closed without them)

    work/ex-minecraft_build/data/action_log.json
      {"builder_a": [{"start_time": "YYYY-MM-DD HH:MM:SS",
                      "end_time": "YYYY-MM-DD HH:MM:SS",
                      "duration": <seconds>, "action": "<what>"}, ...]}
    work/ex-minecraft_build/data/tokens.json
      any non-empty JSON object: your LLM token / cost ledger

At least two entries per agent, and every entry's `duration` must match its own
`start_time`..`end_time` interval within 1 s. The judger computes `efficiency`
from the union of these intervals, so a padded ledger is a self-inflicted low
score and an inconsistent one is refused outright: **no score.json is written,
and the card grades EXTRACT_FAIL rather than passing quietly.**

## 4. Scan and verify

    python3 assets/ex-minecraft_build/judger.py run \
        --task ex-minecraft_build --idx 0 --agent_names builder_a

`run` replays the tape, re-scans the world and reports every mismatch **by
coordinate identity** (`expected X, observed Y`) on stderr, appends a snapshot
to `work/ex-minecraft_build/data/score.json`, and writes

    work/ex-minecraft_build/result/ex-minecraft_build/score.json
      {block_hit_rate, view_hit_rate, efficiency, end_reason, mismatches, strays, ...}

Repair the plan from the mismatch identities and re-run until
`block_hit_rate` is 1.0. `view_hit_rate` scores the facing of the directional
blocks; `strays` lists blocks you left outside the blueprint.

## 5. Grade

From the workspace root, with the card's success command:

    python3 tools/goal_grader.py examples/minecraft_build/card.json <workspace>
