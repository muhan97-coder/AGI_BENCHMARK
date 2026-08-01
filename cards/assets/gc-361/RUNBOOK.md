# gc-361 Runbook (sealed - follow exactly; grading depends on these paths)

All paths are relative to the benchmark repo root.

## 1. Fresh server (never assume a running one)
    docker compose -f assets/gc-361/docker-compose.yml up -d
Wait until the server log prints "Done". The compose file has NO volume:
`docker compose -f assets/gc-361/docker-compose.yml down` discards the world,
so every `up` gives a fresh flat world (ground top at y=-61, builds start at y=-60).

## 2. Judger pipeline (pinned)
    git clone https://github.com/ulab-uiuc/MARBLE work/gc-361/MARBLE
    git -C work/gc-361/MARBLE checkout 8d60fa17b5596b44458a52d4296061b9fc13d6f2
    pip install "javascript==1!1.2.6" numpy==1.26.4 colorlog==6.8.2
    npm install --prefix work/gc-361/MARBLE mineflayer@4.20.1 vec3@0.1.10 minecraft-data@3.59.3 mineflayer-pathfinder@2.4.5
Node 20 is required on PATH (e.g. from docker image node:20.15.1 or a local install).

## 3. Seed the sealed blueprint
    mkdir -p work/gc-361/MARBLE/data work/gc-361/MARBLE/.cache
    cp assets/gc-361/blueprint.json work/gc-361/MARBLE/data/building_blue_print.json
    cp assets/gc-361/blueprint_description.json work/gc-361/MARBLE/data/blueprint_description_all.json
Do NOT edit these two files; the grader assumes the sealed content.

## 4. Launch the judger (one run per task)
    # task 0: 'Oak Frame Hut' (17 blocks) - fresh world first (step 1)
    cd work/gc-361/MARBLE/marble && NODE_PATH=../node_modules PYTHONPATH=.. \
      python3 environments/minecraft_utils/build_judger.py --idx 0 --agent_num 1 --agent_names builder_a --task_name gc-361
The judger connects as bot `build_judge`, clears the arena, stocks the material
chest at world (-4,-60,0), writes the world-space target coordinates to
`work/gc-361/MARBLE/data/map.json`, and ops the agent names passed above.
Wait for `work/gc-361/MARBLE/.cache/load_status.cache` == {"status": "loaded"}
before building.

## 5. Build with your own bots
Connect mineflayer bots (pinned versions above) using EXACTLY the usernames
passed via --agent_names. Materials must be withdrawn from the chest at
(-4,-60,0); target world coordinates come from data/map.json. The judger
re-scans the world every ~10 s and appends progress snapshots to
`work/gc-361/MARBLE/data/score.json` - poll it to verify, then fix mismatches
(wrong block, wrong facing/axis, stray blocks) and re-verify.

## 6. Honest ledgers (REQUIRED - scoring is fail-closed without them)
Maintain during the run:
- `work/gc-361/MARBLE/data/action_log.json`:
  {"<agent_name>": [{"start_time": "YYYY-MM-DD HH:MM:SS", "end_time": "YYYY-MM-DD HH:MM:SS", "duration": <seconds>, "action": "<what>"}, ...]}
  Entries must reflect REAL bot activity; the judger computes the efficiency
  metric from the union of these intervals.
- `work/gc-361/MARBLE/data/tokens.json`: your LLM token/cost ledger (any JSON object).
If either file is missing or empty at completion time the judger cannot write
score.json and the card stays RED.

## 7. Finish
The judger writes `work/gc-361/MARBLE/marble/result/<task_name>/score.json`
(keys: block_hit_rate, view_hit_rate, efficiency, end_reason) when the task
completes or times out. Note: if block_hit_rate does not improve for 600 s the
run is ended ("no better score in wait interval") - plan before you launch,
and keep steady progress. After each task: `docker compose -f assets/gc-361/docker-compose.yml down`.
Grade from the repo root with the card's success command.
