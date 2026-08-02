# mc_bridge — environment access for the `minecraft_build` cards

**This is a hand, not a brain.** It is the plumbing that lets an agent touch a
real Minecraft world — connect a mineflayer bot, read blocks, place a block by
hand or through the server's own `/setblock` and `/fill` commands, pull items
out of a chest — exposed as nine primitives over line-delimited JSON-RPC. It
holds no goal, reads no blueprint, and decides nothing that is scored — where it
must pick something the API forces on it (which face to click when you did not
say), the pick is documented, fixed, and overridable. Every part of a
`minecraft_build` card that is actually *scored* — deciding what to place and in
what order, how to cut a large region into commands, noticing that the world
disagrees with the target, repairing the difference, choosing where to stand —
is deliberately absent, and absent on purpose: writing that plumbing is a tax on
measurement, while deciding what to do with it **is** the measurement.

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
(`--agent_names`), or the judger will not op them and every placement fails —
`place_block` for want of materials, `set_block` and `fill_region` with
`NOT_OPERATOR`.

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
| `connect` | `host`, `port`, `username`, `version="1.19.2"`, `timeout_ms=60000` | `username`, `version`, `position`, `operator` — resolves only after spawn **and** chunk load |
| `disconnect` | — | `disconnected`, `username` |
| `get_position` | — | `position`, `block_position`, `yaw`, `pitch`, `on_ground`, `dimension` |
| `get_inventory` | — | `items[{name,count,slot}]`, `held`, `empty_slots`, `settled` |
| `read_region` | `x1,y1,z1,x2,y2,z2` | `min`, `max`, `count`, `unloaded`, `blocks[{x,y,z,name,loaded,properties}]` |
| `place_block` | `x,y,z,blockName`, `face?`, `look?`, `timeout_ms=20000` | `placed`, `position`, `block`, `properties`, `reference`, `face`, `face_source`, `look` |
| `set_block` | `x,y,z,blockName`, `blockState?`, `confirm_timeout_ms=2000` | `sent`, `position`, `block`, `block_state`, `verified`, `changed`, `state_checked`, `state_match`, `before`, `observed`, `operator`, `waited_ms` |
| `fill_region` | `x1,y1,z1,x2,y2,z2,blockName`, `mode="replace"`, `confirm_timeout_ms=2000` | `sent`, `min`, `max`, `volume`, `limit`, `mode`, `block`, `verified`, `changed`, `probe_position`, `probe_conclusive`, `before`, `observed`, `operator`, `waited_ms` |
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
  disagreement; it does not resolve it. `set_block` and `fill_region` do the
  same, once.
- `settled: false` means the inventory count was still moving when the 2 s cap
  hit — the number is a best effort, not a fact. Unknown is never dressed up as
  known.

## Two hands: `place_block` versus `set_block` / `fill_region`

`place_block` is the bot's physical hand. It needs the item in the bot's
inventory, a solid neighbour to click, and the target within the 4.5-block
survival reach — the same constraints a human player has.

`set_block` and `fill_region` send Minecraft's own `/setblock` and `/fill`
server commands. They are a public part of the game, not something this
benchmark invented, and they change the shape of what is possible: no
inventory, no support block, no reach limit, and one `/fill` writes up to 32768
blocks at once. Measured on one local run against the pinned 1.19.2 image, 120
back-to-back `set_block` calls ran at **18.5 blocks/s** (each waits for its own
confirming read), while a single 32×32×32 `fill_region` wrote **32768 blocks in
0.50 s** — treat those as an order of magnitude, not a promise.

**Both need operator permission.** A server silently ignores `/setblock` and
`/fill` from a non-op — no error, no effect — which is exactly the kind of quiet
failure that ruins an episode log. So the bridge reads the command tree the
server sends each client (it is filtered by permission level, and re-sent when
that level changes), and returns `NOT_OPERATOR` with the command it sent and
both reads attached, rather than reporting a success that never happened.
`connect` reports the same thing up front as `operator: true | false | null`.

How op is granted:

- **On the scored cards**, the compose file ops only the judger bot
  (`OPS: "build_judge"`); the judger then ops each name passed to
  `--agent_names`. That is why your bots must connect with exactly those
  usernames — a mismatch leaves them un-opped.
- **On a throwaway server of your own**, `rcon-cli op <name>` after the bot has
  joined is the reliable route, because the server then has the bot's real
  offline-mode profile. Beware the name-based `OPS` env var on an
  `ONLINE_MODE=FALSE` server: it is resolved through an account lookup, so a
  username that matches a registered Minecraft account is written into
  `ops.json` under that account's UUID — which your offline bot never has, so
  it joins un-opped while the file looks correct.

Two more properties worth knowing before you build on them:

- `blockState` is **your** string, dropped in verbatim between the brackets the
  command syntax needs: `"axis=x"` and `"[axis=x]"` both produce
  `/setblock 10 -60 10 oak_log[axis=x]`. The bridge never picks, reorders or
  completes a property, because axis and facing are graded. It does check what
  came back: `state_match` is `true`/`false`, or `null` when you asked for
  nothing or the string was not a plain `key=value` list.
- Verification is a **single read**, and it can honestly fail to happen. A cell
  outside the chunks this client has loaded comes back `verified: null` with
  `unverified_reason`: the command went out, but the bridge cannot see the
  result — and vanilla itself refuses to write into a chunk the *server* has not
  loaded ("That position is not loaded"), so far-flung writes may not land at
  all. Unknown is returned as unknown, never as success.
  `fill_region` confirms one cell, the corner you named as
  `x1,y1,z1`, and says so via `probe_position`; in `keep` mode that corner
  proves nothing either way, which is reported as `probe_conclusive: false`
  rather than guessed at. If you want to know what the whole box holds, that is
  what `read_region` is for.

## What it deliberately does **not** do

Each row is a capability a `minecraft_build` card exists to measure. Shipping
it here would mean the benchmark scoring its own code:

| not provided | why it stays on your side |
| --- | --- |
| reading or parsing any card file (`blueprint.json`, `map.json`, …) | the bridge touches no files at all; every coordinate it acts on is one the caller passed in, in world space |
| deciding *what* to place, and in what **order** | this is the plan artifact `process_expectations` require before the first block; it is the planning axis. Commands go out in the order you call them — never sorted, never bottom-up, never dependency-ordered |
| **splitting** an oversized region into batches | `fill_region` refuses anything past vanilla's 32768-block limit with `FILL_VOLUME_EXCEEDED` and the volume attached. Deciding where to cut a big build and which piece goes first *is* the build plan; a bridge that chunked it for you would be writing the plan |
| comparing world against target, detecting mismatches | verification. The judger's snapshot feed gives you readings; turning readings into failure *identities* (coordinate, expected, observed) is scored, and a count would not do |
| repairing a wrong block, wrong facing, or a stray | the recovery axis is precisely the RED → repair → GREEN chain. A bridge that auto-fixed would erase the axis. `set_block` and `fill_region` re-read once and hand you `PLACED_MISMATCH`; neither re-sends |
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
| server commands | `NOT_OPERATOR`, `FILL_VOLUME_EXCEEDED`, `COMMAND_TOO_LONG`, `PLACED_MISMATCH` |
| chests | `UNKNOWN_ITEM`, `CONTAINER_OPEN_FAILED`, `OPEN_TIMEOUT`, `INSUFFICIENT_STOCK`, `WITHDRAW_TIMEOUT`, `WITHDRAW_FAILED` |
| Python client only | `BRIDGE_DEAD` (the node process exited), `PROTOCOL_DESYNC` (frame id mismatch) |

`detail` carries the observation that produced the code: `TARGET_OCCUPIED` ships
`observed`, `OUT_OF_REACH` ships `distance`/`reach`/`bot_position`,
`ITEM_NOT_IN_INVENTORY` ships the full inventory snapshot,
`INSUFFICIENT_STOCK` ships `available` and the chest contents,
`NO_ADJACENT_SUPPORT` ships the six neighbours it checked,
`NOT_OPERATOR` ships the exact command text plus the before/after reads, and
`FILL_VOLUME_EXCEEDED` ships `volume` and `limit` so you can decide how to cut
the region — the decision the bridge refuses to make for you.

`blockName` must be one bare token (`stone_bricks`, `minecraft:oak_log`) and
`blockState` may not contain a space or a control character; both are rejected
with `BAD_PARAMS` rather than quoted, escaped or repaired, so a command can
never turn into two and a stray token can never become a command's next
argument.

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

`--commands` adds the server-command primitives, which need op but no stock:

```sh
python3 smoke_test.py --port 25565 --username builder_a --commands --skip-place \
    --gear-cmd 'docker exec gc-360-mc rcon-cli op builder_a'
```

That section runs three `set_block` calls (one with a caller-chosen
`axis=x`, one 40 blocks out to show the reach limit is gone), one 3×1×3
`fill_region`, a `read_region` over the result, and one deliberately oversized
`fill_region` so you can see it refused rather than split. Run it *without* op
and every call that reaches the server comes back `NOT_OPERATOR` instead —
which is the point of the code existing. The oversized fill is the exception:
its volume is checked before anything is sent, so it returns
`FILL_VOLUME_EXCEEDED` whether you are op or not.

## Where it fits in a card run

Against `cards/assets/gc-360/RUNBOOK.md`: phases 1–4 (fresh server, pinned
MARBLE judger, sealed blueprint, judger launch) are the card's own setup and
the bridge takes no part in them. Phase 5 — *build with your own bots* — is the
only place it appears, and it appears as a hand: your planner reads
`data/map.json`, decides an order, and calls `place_block` — or, once the
judger has opped your bots, `set_block` and `fill_region`. Phases 6–7 (honest
ledgers, judger scoring) are yours again. The bridge never reads the judger's
snapshot feed and never writes anything to disk.
