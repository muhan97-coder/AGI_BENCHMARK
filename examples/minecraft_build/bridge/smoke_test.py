"""Live smoke test for the bridge: connect, stock, place 3 blocks, read back, leave.

It proves the access layer works against a real server. It is not a solver and
it does not read any blueprint -- the coordinates are derived from wherever the
bot happens to spawn.

    # server on 25565, bot stocked through the server console (rcon)
    python3 smoke_test.py --port 25565 --username bridge_bot \
        --gear-cmd 'docker exec <container> rcon-cli give bridge_bot stone_bricks 64'

`--gear-cmd` runs once, after the bot is online, so the server can see it. It is
your own string and it runs through your shell, exactly as if you had typed it;
its exit code and stderr are printed rather than swallowed.
`--chest x,y,z` additionally exercises withdraw_from_chest at that position.

`--commands` additionally exercises the two server-command primitives, which
need no inventory but do need operator permission:

    python3 smoke_test.py --port 25565 --username bridge_bot --commands \
        --gear-cmd 'docker exec <container> rcon-cli op bridge_bot'

Run it without op and every set_block/fill_region call that reaches the server
comes back NOT_OPERATOR, which is the honest answer rather than a silent no-op.
(The oversized fill is refused locally as FILL_VOLUME_EXCEEDED either way: the
volume is checked before anything is sent.)
"""

from __future__ import annotations

import argparse
import json
import subprocess

from mc_bridge import BridgeError, McBridge


def show(label: str, value) -> None:
    print(f"--- {label}\n{json.dumps(value, indent=2, sort_keys=True)}")


def attempt(label: str, call) -> None:
    """Run one bridge call and print whichever answer comes back."""
    try:
        show(label, call())
    except BridgeError as e:
        show(f"{label} FAILED", {"code": e.code, "message": e.message, "detail": e.detail})


def server_commands(mc: McBridge, bx: int, by: int, bz: int, block: str) -> None:
    """Exercise set_block and fill_region: no inventory, no reach, op required."""
    attempt(f"set_block {bx + 4},{by},{bz}", lambda: mc.set_block(bx + 4, by, bz, block))
    # A block state the caller chose. The bridge passes "axis=x" through and
    # then reports what the server actually stored.
    attempt(f"set_block {bx + 5},{by},{bz} axis=x", lambda: mc.set_block(bx + 5, by, bz, "oak_log", "axis=x"))
    # 40 blocks out: far past the 4.5-block reach place_block is bound by.
    attempt(f"set_block {bx + 40},{by},{bz} (far)", lambda: mc.set_block(bx + 40, by, bz, block))

    attempt(
        f"fill_region {bx + 4},{by + 1},{bz} .. {bx + 6},{by + 1},{bz + 2}",
        lambda: mc.fill_region(bx + 4, by + 1, bz, bx + 6, by + 1, bz + 2, block),
    )
    show("read_region (filled box)", mc.read_region(bx + 4, by + 1, bz, bx + 6, by + 1, bz + 2))

    # 32 x 32 x 33 = 33792 blocks: over vanilla's /fill limit, so it is refused
    # with the numbers rather than quietly split into batches.
    attempt(
        "fill_region (over the volume limit)",
        lambda: mc.fill_region(bx, by, bz, bx + 31, by + 31, bz + 32, block),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=25565)
    ap.add_argument("--username", default="bridge_bot")
    ap.add_argument("--block", default="stone_bricks")
    ap.add_argument("--gear-cmd", default=None, help="shell command run after connect, to stock the bot")
    ap.add_argument("--chest", default=None, help="x,y,z of a stocked chest to test withdraw_from_chest")
    ap.add_argument("--commands", action="store_true", help="also exercise set_block/fill_region (needs op)")
    ap.add_argument("--skip-place", action="store_true", help="skip the place_block section, which needs stock")
    args = ap.parse_args()

    with McBridge() as mc:
        show("connect", mc.connect(args.host, args.port, args.username))
        pos = mc.get_position()
        show("get_position", pos)

        if args.gear_cmd:
            print(f"--- gear-cmd\n{args.gear_cmd}")
            r = subprocess.run(args.gear_cmd, shell=True, capture_output=True, text=True)
            # A failed stocking command must not read as a success and then
            # resurface as a confusing ITEM_NOT_IN_INVENTORY three lines later.
            show("gear-cmd result", {"returncode": r.returncode,
                                     "stdout": r.stdout.strip(), "stderr": r.stderr.strip()})

        if args.chest:
            cx, cy, cz = (int(v) for v in args.chest.split(","))
            show("withdraw_from_chest", mc.withdraw_from_chest(cx, cy, cz, args.block, 3))

        show("get_inventory", mc.get_inventory())

        bx, by, bz = (pos["block_position"][k] for k in "xyz")
        if not args.skip_place:
            targets = [(bx + 1, by, bz), (bx + 2, by, bz), (bx + 1, by, bz + 1)]
            for tx, ty, tz in targets:
                attempt(f"place_block {tx},{ty},{tz}", lambda t=(tx, ty, tz): mc.place_block(*t, args.block))

            xs = [t[0] for t in targets]
            zs = [t[2] for t in targets]
            show("read_region", mc.read_region(min(xs), by, min(zs), max(xs), by, max(zs)))
            show("get_inventory (after)", mc.get_inventory())

        if args.commands:
            server_commands(mc, bx, by, bz, args.block)

        show("disconnect", mc.disconnect())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
