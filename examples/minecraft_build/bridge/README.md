# mc_bridge — environment access for the `minecraft_build` cards

**This is a hand, not a brain.** It is the plumbing that lets an agent touch a
real Minecraft world — connect a mineflayer bot, read blocks, place a block,
pull items out of a chest — exposed as seven primitives over line-delimited
JSON-RPC. It holds no goal, reads no blueprint, and decides nothing that is
scored — where it must pick something the API forces on it (which face to click
when you did not say), the pick is documented, fixed, and overridable. Every
part of a `minecraft_build` card that is actually *scored* — deciding what to
place and in what order, noticing that the world disagrees with the target,
repairing the difference, choosing where to stand — is deliberately absent, and
absent on purpose: writing that plumbing is a tax on measurement, while
deciding what to do with it **is** the measurement.

It ships publicly for the reason set out in the root README under *What we ship
and what we don't*: environment access is public, task strategy is private. A
benchmark where only its authors own the plumbing is not measuring capability,
it is measuring who wrote the plumbing.

Scope note: the scored cards `gc-360 … gc-371` are what this exists for. The
teaching demo one directory up (`examples/minecraft_build/`) is a simulated
arena that runs offline in under a second and does **not** use the bridge —
learn the grading contract there, come here when you want the real world.

---

## Install

Node 20, and the same pins the card runbooks specify
(`mineflayer@4.20.1`, `vec3@0.1.10`, `minecraft-data@3.59.3` — see
`package.json`):

```sh
cd examples/minecraft_build/bridge
npm install
```

Verify the install and the bridge itself without a server, offline:

```sh
node -e "require('mineflayer'); console.log('mineflayer ok')"

echo '{"id":0,"method":"get_position","params":{}}' | node mc_bridge.js
# {"id":0,"ok":false,"error":{"code":"NOT_CONNECTED","message":"No bot is connected; call connect first","detail":{}}}
```

That error frame *is* the success signal: the process came up, parsed a
request, dispatched it and refused it honestly.

## A world to talk to

The scored cards bring their own pinned server; nothing here does it for you:

```sh
docker compose -f cards/assets/gc-360/docker-compose.yml up -d   # port 25565, fresh flat world
# ... run the card ...
docker compose -f cards/assets/gc-360/docker-compose.yml down    # no volume: the world is discarded
```

Bots must connect with **exactly** the usernames the judger was launched with
(`--agent_names`), or the judger will not op them and every placement fails.

## Use it from Python

`mc_bridge.py` owns one `node mc_bridge.js` subprocess and turns error frames
into `BridgeError`. One call, one round trip, no added logic.

```sh
PYTHONPATH=examples/minecraft_build/bridge python3 - <<'PY'
from mc_bridge import McBridge, BridgeError

with McBridge() as mc:
    print(mc.connect("127.0.0.1", 25565, "builder_a"))
    print(mc.withdraw_from_chest(-4, -60, 0, "stone_bricks", 6))
    try:
        print(mc.place_block(0, -60, 0, "stone_bricks"))
    except BridgeError as e:
        print(e.code, e.detail)      # TARGET_OCCUPIED {'observed': 'dirt'} -> your move
    region = mc.read_region(0, -60, 0, 2, -60, 1)
    print(region["count"], region["blocks"][0])
PY
```

The `except` branch is the whole design in miniature. `TARGET_OCCUPIED` with
the observed block name attached is data; deciding to break the dirt, place
elsewhere, or halt is strategy, and strategy is yours.

## Use it from Node (or any language)

The protocol is one JSON object per line in each direction. `stdout` carries
protocol frames **exclusively**; logs go to `stderr`.

```sh
cd examples/minecraft_build/bridge
printf '%s\n' \
  '{"id":1,"method":"connect","params":{"host":"127.0.0.1","port":25565,"username":"builder_a"}}' \
  '{"id":2,"method":"get_position","params":{}}' \
  '{"id":3,"method":"read_region","params":{"x1":0,"y1":-60,"z1":0,"x2":2,"y2":-60,"z2":1}}' \
  | node mc_bridge.js
```

```jsonc
// ->
{"id": 1, "method": "place_block", "params": {"x": 0, "y": -60, "z": 0, "blockName": "stone_bricks"}}
// <- success
{"id": 1, "ok": true,  "result": {"placed": true, "block": "stone_bricks", "properties": {}, ...}}
// <- failure
{"id": 1, "ok": false, "error": {"code": "OUT_OF_REACH", "message": "...", "detail": {"distance": 7.2, "reach": 4.5, "bot_position": {...}}}}
```

Requests are serialised: one world action at a time, in arrival order. One
bridge process owns exactly one bot — for the multi-bot cards (gc-364 twin
towers, gc-369 three-bot bastion) run one bridge per bot and coordinate them
yourself.

## Primitives

| method | params | returns |
| --- | --- | --- |
| `connect` | `host`, `port`, `username`, `version="1.19.2"`, `timeout_ms=60000` | `username`, `version`, `position` — resolves only after spawn **and** chunk load |
| `disconnect` | — | `disconnected`, `username` |
| `get_position` | — | `position`, `block_position`, `yaw`, `pitch`, `on_ground`, `dimension` |
| `get_inventory` | — | `items[{name,count,slot}]`, `held`, `empty_slots`, `settled` |
| `read_region` | `x1,y1,z1,x2,y2,z2` | `min`, `max`, `count`, `unloaded`, `blocks[{x,y,z,name,loaded,properties}]` |
| `place_block` | `x,y,z,blockName`, `face?`, `look?`, `timeout_ms=20000` | `placed`, `position`, `block`, `properties`, `reference`, `face`, `face_source`, `look` |
| `withdraw_from_chest` | `x,y,z,itemName,count`, `timeout_ms=20000` | `withdrawn`, `item`, `requested`, `inventory_count`, `settled` |

Notes that matter for grading:

- `read_region` passes **raw block state** through under `properties`
  (`facing`, `axis`, `half`, …) with no interpretation. The cards grade facing
  and axis; the bridge refuses to have an opinion about them.
- Which face you click and where you look are what the *server* derives
  `axis`/`facing`/`half` from, so `place_block` hands both to you:
  `face` is a unit axis vector naming the neighbour face to click
  (`{"x":0,"y":1,"z":0}` = click the top of the block below, i.e. place from
  above), `look` is a world point to face first. Omit them and the bridge clicks
  the first solid neighbour in a fixed order — down, up, −x, +x, −z, +z — and
  looks at the target centre. The reply reports `face_source: "caller"` or
  `"auto"` so your log records who decided. A bridge that chose the axis for you
  would be answering `gc-361`/`gc-363` on your behalf.
- Regions are capped at 32768 blocks (`REGION_TOO_LARGE`). Blocks in unloaded
  chunks come back as `{"name": null, "loaded": false}` and are counted in
  `unloaded` — never silently as air.
- `place_block` re-reads the cell after placing and raises `PLACED_MISMATCH` if
  the server disagrees with what you asked for. It **reports** the
  disagreement; it does not resolve it.
- `settled: false` means the inventory count was still moving when the 2 s cap
  hit — the number is a best effort, not a fact. Unknown is never dressed up as
  known.

## What it deliberately does **not** do

Each row is a capability a `minecraft_build` card exists to measure. Shipping
it here would mean the benchmark scoring its own code:

| not provided | why it stays on your side |
| --- | --- |
| reading or parsing `blueprint.json` / `map.json` | translating blueprint-relative coordinates into world space through `map.json` is the card's central trap — a plan written from the blueprint alone lands a block short |
| deciding *what* to place, and in what **order** | this is the plan artifact `process_expectations` require before the first block; it is the planning axis |
| comparing world against target, detecting mismatches | verification. The judger's snapshot feed gives you readings; turning readings into failure *identities* (coordinate, expected, observed) is scored, and a count would not do |
| repairing a wrong block, wrong facing, or a stray | the recovery axis is precisely the RED → repair → GREEN chain. A bridge that auto-fixed would erase the axis |
| pathfinding, or **any** movement of the bot | where to stand is a decision. `OUT_OF_REACH` comes back as data with `distance`, `reach` and `bot_position` attached. The cards pin `mineflayer-pathfinder@2.4.5` in their own resource list — if you want locomotion, that layer is yours to add, and the bridge has no dependency on it |
| retrying, backing off, or recovering from a failed action | a hidden retry loop would inflate recovery and hide honest failures from the episode log |
| withdrawing "what you'll need" | it withdraws exactly what you asked for. Chest stock is exact on the scored cards, so over-withdrawal is a real, scored mistake |
| writing `action_log.json` / `tokens.json` | those ledgers are the honesty axis and the judger enforces them; a tool that wrote them for you would be forging your own telemetry |

Nothing is silently swallowed and nothing is silently fixed. Every failure
returns a typed code with the observed state attached, so your agent has enough
to decide — and so the decision is visible in your logs.

## Connection safety and process lifetime

- **No credentials, ever.** The bot always connects in mineflayer's `offline`
  auth mode; there is no code path that reads, prompts for or accepts a
  Microsoft/Mojang account, a token or a password. It is built for
  unauthenticated local test servers — the cards' compose file sets
  `ONLINE_MODE=FALSE` — and `host` defaults to `127.0.0.1`.
- **You pick the host, and you should pick your own.** Pointing this at a
  server you do not run is your call and outside what the cards ask for; the
  scored cards each stand up their own throwaway world on localhost.
- **One process, one bot, and it always leaves.** The bridge exits when stdin
  closes and on `SIGINT`/`SIGTERM`/`SIGHUP`, quitting the bot on the way out;
  a stdout that goes away (`EPIPE`) is also a clean exit rather than a wedge. In
  Python, `with McBridge() as mc:` closes stdin on the way out and kills **and
  reaps** the child if it does not leave within 15 s, so no bridge is left
  holding a session.
- **Nothing is written to disk.** The bridge reads no files, writes no files,
  opens no network listener, and never touches the judger's snapshot feed.

## Error codes

| group | codes |
| --- | --- |
| connection | `NOT_CONNECTED`, `ALREADY_CONNECTED`, `CONNECT_FAILED`, `CONNECT_TIMEOUT`, `KICKED`, `CHUNK_LOAD_TIMEOUT` |
| protocol | `BAD_JSON`, `BAD_PARAMS`, `UNKNOWN_METHOD`, `INTERNAL_ERROR` |
| reading | `REGION_TOO_LARGE`, `CHUNK_NOT_LOADED` |
| placing | `TARGET_OCCUPIED`, `OUT_OF_REACH`, `ITEM_NOT_IN_INVENTORY`, `NO_ADJACENT_SUPPORT`, `EQUIP_TIMEOUT`, `LOOK_TIMEOUT`, `PLACE_TIMEOUT`, `PLACE_FAILED`, `PLACED_MISMATCH` |
| chests | `UNKNOWN_ITEM`, `CONTAINER_OPEN_FAILED`, `OPEN_TIMEOUT`, `INSUFFICIENT_STOCK`, `WITHDRAW_TIMEOUT`, `WITHDRAW_FAILED` |
| Python client only | `BRIDGE_DEAD` (the node process exited), `PROTOCOL_DESYNC` (frame id mismatch) |

`detail` carries the observation that produced the code: `TARGET_OCCUPIED` ships
`observed`, `OUT_OF_REACH` ships `distance`/`reach`/`bot_position`,
`ITEM_NOT_IN_INVENTORY` ships the full inventory snapshot,
`INSUFFICIENT_STOCK` ships `available` and the chest contents,
`NO_ADJACENT_SUPPORT` ships the six neighbours it checked.

## Why inventory counts are treated as suspect

mineflayer's client-side inventory lags the server by a tick or two after an
action, and while a chest window is open the player's slots belong to that
window rather than to `bot.inventory` — read it at the wrong moment and you get
a confident zero. `get_inventory` and `withdraw_from_chest` therefore wait for
slot updates to go quiet (300 ms quiet, 2 s cap) before reporting, and return
`settled: false` rather than pretending a number is final. This is transport
synchronisation of a single call, not a retry: nothing is re-attempted.

## Smoke test against a live server

```sh
cd examples/minecraft_build/bridge
python3 smoke_test.py --port 25565 --username builder_a \
    --gear-cmd 'docker exec gc-360-mc rcon-cli give builder_a stone_bricks 64'
```

One bot connects, optionally gets stocked, places three blocks next to wherever
it spawned, reads them back and leaves. Add `--chest x,y,z` to exercise
`withdraw_from_chest` against a stocked chest instead. No blueprint is involved
and no target is compared — the coordinates come from the bot's own spawn
position, because this proves the *hand* works, nothing more.

## Where it fits in a card run

Against `cards/assets/gc-360/RUNBOOK.md`: phases 1–4 (fresh server, pinned
MARBLE judger, sealed blueprint, judger launch) are the card's own setup and
the bridge takes no part in them. Phase 5 — *build with your own bots* — is the
only place it appears, and it appears as a hand: your planner reads
`data/map.json`, decides an order, and calls `place_block`. Phases 6–7 (honest
ledgers, judger scoring) are yours again. The bridge never reads the judger's
snapshot feed and never writes anything to disk.
