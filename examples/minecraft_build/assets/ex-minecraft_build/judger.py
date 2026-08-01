#!/usr/bin/env python3
"""build_judger, miniature edition (SEALED, do not modify).

Stands in for the MARBLE ``build_judger`` pipeline of the scored
minecraft_build cards. Instead of driving a real Minecraft server with
mineflayer bots over docker, it hosts a *simulated* arena: the agent ships a
build plan (the bot's action tape), the judger replays it against the arena,
re-scans the resulting world and scores it against the sealed blueprint.

Everything that makes the scored cards hard survives the shrink:

  * blueprint coordinates are blueprint-relative; the judger shifts them into
    world space and only publishes the world coordinates in data/map.json;
  * materials come from a chest with an EXACT stock -- wasted placements run
    the inventory dry;
  * the arena is not empty: prepare drops an obstruction the plan must break
    before it can place, so a plan written from the blueprint alone falls short;
  * directional blocks carry a facing that is scored separately (view_hit_rate);
  * the honest ledgers (data/action_log.json, data/tokens.json) are REQUIRED:
    without consistent ledgers the judger refuses to write score.json at all,
    so the card stays red by way of EXTRACT_FAIL rather than a silent pass.

Usage (from the workspace root):
  python3 assets/ex-minecraft_build/judger.py prepare --task ex-minecraft_build \\
      --idx 0 --agent_names builder_a
  python3 assets/ex-minecraft_build/judger.py run --task ex-minecraft_build \\
      --idx 0 --agent_names builder_a
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLUEPRINT = os.path.join(HERE, "blueprint.json")
GROUND_Y = -61              # top of the flat world; builds start one block above
ORIGIN = (0, GROUND_Y + 1, 0)
CHEST = [-4, GROUND_Y + 1, 0]
# The arena is pre-existing terrain, not a blank slate: one block squats on a
# blueprint cell and must be broken before the right block can go there.
OBSTRUCTIONS = [{"pos": [0, GROUND_Y + 1, 1], "name": "dirt"}]
TS_FMT = "%Y-%m-%d %H:%M:%S"


class Refuse(Exception):
    """The judger cannot score this run; score.json is NOT written."""


def key(pos):
    return "%d,%d,%d" % (int(pos[0]), int(pos[1]), int(pos[2]))


def run_dir(task):
    return os.path.join("work", task)


def read_json(path, what):
    try:
        with open(path) as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise Refuse("%s missing: %s" % (what, path))
    except ValueError as err:
        raise Refuse("%s is not valid JSON (%s): %s" % (what, err, path))


# --------------------------------------------------------------------------- prepare


def cmd_prepare(args):
    with open(BLUEPRINT) as fh:
        structures = json.load(fh)
    if not 0 <= args.idx < len(structures):
        raise Refuse("no structure at --idx %d" % args.idx)
    structure = structures[args.idx]
    targets, materials = [], {}
    for block in structure["blocks"]:
        bx, by, bz = block["position"]
        targets.append({"pos": [bx + ORIGIN[0], by + ORIGIN[1], bz + ORIGIN[2]],
                        "name": block["name"], "facing": block.get("facing", "A")})
        materials[block["name"]] = materials.get(block["name"], 0) + 1
    base = run_dir(args.task)
    os.makedirs(os.path.join(base, "data"), exist_ok=True)
    os.makedirs(os.path.join(base, ".cache"), exist_ok=True)
    world_map = {
        "task": args.task, "structure": structure["name"], "idx": args.idx,
        "agents": args.agent_names, "ground_y": GROUND_Y, "origin": list(ORIGIN),
        "chest": CHEST, "chest_stock": materials,
        "arena_blocks": OBSTRUCTIONS, "targets": targets,
    }
    with open(os.path.join(base, "data", "map.json"), "w") as fh:
        json.dump(world_map, fh, indent=1)
    # A fresh arena invalidates every earlier reading.
    with open(os.path.join(base, "data", "score.json"), "w") as fh:
        json.dump([], fh)
    result = os.path.join(base, "result", args.task, "score.json")
    if os.path.exists(result):
        os.remove(result)
    with open(os.path.join(base, ".cache", "load_status.cache"), "w") as fh:
        json.dump({"status": "loaded"}, fh)
    print("arena ready: '%s', %d target blocks, chest at %s stocked %s"
          % (structure["name"], len(targets), CHEST, json.dumps(materials, sort_keys=True)))
    print("pre-existing arena blocks (scan before you place): %s" % json.dumps(OBSTRUCTIONS))
    print("world coordinates written to %s"
          % os.path.join(base, "data", "map.json").replace(os.sep, "/"))
    return 0


# --------------------------------------------------------------------------- ledgers


def check_ledgers(base, agents):
    """Fail-closed honesty gate on the two ledgers the judger needs."""
    log = read_json(os.path.join(base, "data", "action_log.json"), "action ledger")
    if not isinstance(log, dict) or not log:
        raise Refuse("action ledger must be an object mapping agent name -> entries")
    for agent in agents:
        if agent not in log:
            raise Refuse("action ledger has no entries for agent %r" % agent)
    active = []
    for agent, entries in log.items():
        if not isinstance(entries, list) or len(entries) < 2:
            raise Refuse("action ledger for %r needs at least 2 real entries" % agent)
        for i, entry in enumerate(entries):
            try:
                start = dt.datetime.strptime(entry["start_time"], TS_FMT)
                end = dt.datetime.strptime(entry["end_time"], TS_FMT)
                claimed = float(entry["duration"])
                action = str(entry["action"])
            except (KeyError, TypeError, ValueError) as err:
                raise Refuse("action ledger %r entry %d malformed: %r" % (agent, i, err))
            real = (end - start).total_seconds()
            if real < 0:
                raise Refuse("action ledger %r entry %d ends before it starts" % (agent, i))
            if abs(real - claimed) > 1.0:
                raise Refuse("action ledger %r entry %d claims duration %.0f s but the "
                             "interval %s..%s is %.0f s"
                             % (agent, i, claimed, entry["start_time"], entry["end_time"], real))
            if not action:
                raise Refuse("action ledger %r entry %d has an empty action" % (agent, i))
            active.append((start, end))
    tokens = read_json(os.path.join(base, "data", "tokens.json"), "token ledger")
    if not isinstance(tokens, dict) or not tokens:
        raise Refuse("token ledger must be a non-empty JSON object")
    # union of the active intervals, in seconds
    total, cursor = 0.0, None
    for start, end in sorted(active):
        if cursor is None or start > cursor:
            total += (end - start).total_seconds()
            cursor = end
        elif end > cursor:
            total += (end - cursor).total_seconds()
            cursor = end
    return total


# --------------------------------------------------------------------------- run


def simulate(plan, world_map):
    """Replay the action tape against the arena. Returns (world, inventory, errors)."""
    world = {key(b["pos"]): {"name": b["name"], "facing": "A"} for b in world_map["arena_blocks"]}
    chest = dict(world_map["chest_stock"])
    inventory, errors = {}, []
    actions = plan.get("actions")
    if not isinstance(actions, list) or not actions:
        raise Refuse("build plan has no 'actions' list")
    for i, act in enumerate(actions):
        if not isinstance(act, dict):
            raise Refuse("build plan action %d is not an object" % i)
        verb = act.get("t")
        if verb == "withdraw":
            item, want = act.get("item"), int(act.get("count", 0))
            have = chest.get(item, 0)
            take = max(0, min(want, have))
            if take < want:
                errors.append("action %d: chest holds %d %s, plan withdrew %d"
                              % (i, have, item, want))
            chest[item] = have - take
            inventory[item] = inventory.get(item, 0) + take
        elif verb == "place":
            pos, block = act.get("pos"), act.get("block")
            if pos is None or block is None:
                raise Refuse("build plan action %d: place needs 'pos' and 'block'" % i)
            if inventory.get(block, 0) <= 0:
                errors.append("action %d: no %s in inventory to place at %s" % (i, block, pos))
                continue
            if key(pos) in world:
                errors.append("action %d: %s is occupied by %s -- break it first"
                              % (i, pos, world[key(pos)]["name"]))
                continue
            inventory[block] -= 1
            world[key(pos)] = {"name": block, "facing": act.get("facing", "A")}
        elif verb == "break":
            pos = act.get("pos")
            if pos is None:
                raise Refuse("build plan action %d: break needs 'pos'" % i)
            existing = world.pop(key(pos), None)
            if existing is None:
                errors.append("action %d: nothing to break at %s" % (i, pos))
                continue
            inventory[existing["name"]] = inventory.get(existing["name"], 0) + 1
        else:
            raise Refuse("build plan action %d: unknown verb %r (place|break|withdraw)"
                         % (i, verb))
    return world, inventory, errors


def cmd_run(args):
    base = run_dir(args.task)
    status = read_json(os.path.join(base, ".cache", "load_status.cache"), "arena status")
    if status.get("status") != "loaded":
        raise Refuse("arena is not loaded -- run 'judger.py prepare' first")
    world_map = read_json(os.path.join(base, "data", "map.json"), "world map")
    plan = read_json(os.path.join(base, "data", "build_plan.json"), "build plan")
    active_s = check_ledgers(base, args.agent_names)
    world, inventory, errors = simulate(plan, world_map)

    targets = world_map["targets"]
    matched, view_total, view_ok, mismatches = 0, 0, 0, []
    for target in targets:
        observed = world.get(key(target["pos"]))
        directional = target.get("facing", "A") != "A"
        if observed is None:
            mismatches.append("%s expected %s, observed <empty>" % (target["pos"], target["name"]))
        elif observed["name"] != target["name"]:
            mismatches.append("%s expected %s, observed %s"
                              % (target["pos"], target["name"], observed["name"]))
        else:
            matched += 1
            if directional:
                if observed.get("facing") == target["facing"]:
                    view_ok += 1
                else:
                    mismatches.append("%s %s expected facing %s, observed %s"
                                      % (target["pos"], target["name"], target["facing"],
                                         observed.get("facing")))
        if directional:
            view_total += 1
    target_keys = {key(t["pos"]) for t in targets}
    strays = sorted(k for k in world if k not in target_keys)

    block_hit_rate = round(matched / float(len(targets)), 6)
    view_hit_rate = round(view_ok / float(view_total), 6) if view_total else 1.0
    efficiency = round(matched / (active_s / 60.0), 3) if active_s > 0 else 0.0
    end_reason = "task_complete" if block_hit_rate >= 1.0 else "plan_exhausted"

    snapshot = {"ts": dt.datetime.now().strftime(TS_FMT), "block_hit_rate": block_hit_rate,
                "view_hit_rate": view_hit_rate, "mismatches": mismatches, "strays": strays}
    snaps_path = os.path.join(base, "data", "score.json")
    try:
        snaps = read_json(snaps_path, "snapshot feed")
    except Refuse:
        snaps = []
    snaps.append(snapshot)
    with open(snaps_path, "w") as fh:
        json.dump(snaps, fh, indent=1)

    score = {"task": args.task, "structure": world_map["structure"],
             "block_hit_rate": block_hit_rate, "view_hit_rate": view_hit_rate,
             "efficiency": efficiency, "end_reason": end_reason,
             "blocks_matched": matched, "blocks_total": len(targets),
             "strays": strays, "mismatches": mismatches,
             "plan_errors": errors, "leftover_inventory":
                 {k: v for k, v in sorted(inventory.items()) if v},
             "active_seconds": round(active_s, 1)}
    out = os.path.join(base, "result", args.task)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "score.json"), "w") as fh:
        json.dump(score, fh, indent=1)

    for err in errors:
        print("plan error: %s" % err, file=sys.stderr)
    for miss in mismatches:
        print("mismatch: %s" % miss, file=sys.stderr)
    for stray in strays:
        print("stray block at %s" % stray, file=sys.stderr)
    print(json.dumps({"block_hit_rate": block_hit_rate, "view_hit_rate": view_hit_rate,
                      "efficiency": efficiency, "end_reason": end_reason}))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(prog="judger", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, func in (("prepare", cmd_prepare), ("run", cmd_run)):
        p = sub.add_parser(name)
        p.add_argument("--task", default="ex-minecraft_build")
        p.add_argument("--idx", type=int, default=0)
        p.add_argument("--agent_names", nargs="+", default=["builder_a"])
        p.set_defaults(func=func)
    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except Refuse as err:
        print("judger refuses to score this run: %s" % err, file=sys.stderr)
        print("score.json was NOT written (fail-closed)", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
