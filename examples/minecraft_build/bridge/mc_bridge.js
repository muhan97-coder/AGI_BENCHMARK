#!/usr/bin/env node
/**
 * mc_bridge.js - raw mineflayer primitives over line-delimited JSON-RPC (stdio).
 *
 * This is an ACCESS LAYER, not an agent. It exposes the smallest set of
 * world operations a builder needs and nothing else. It does not read
 * blueprints, choose placement order, detect or repair mismatches, plan
 * paths, or retry. Those are the things the minecraft_build cards measure,
 * so they stay on the agent's side of the line.
 *
 * Protocol (one JSON object per line, both directions):
 *   ->  {"id": 1, "method": "place_block", "params": {...}}
 *   <-  {"id": 1, "ok": true,  "result": {...}}
 *   <-  {"id": 1, "ok": false, "error": {"code": "...", "message": "...", "detail": {...}}}
 *
 * Methods: connect, disconnect, get_position, get_inventory,
 *          read_region, place_block, set_block, fill_region,
 *          withdraw_from_chest.
 *
 * set_block and fill_region send Minecraft's own `/setblock` and `/fill`
 * server commands, which need operator permission but no inventory and no
 * reach. They send exactly one command, read the world back once and report
 * what they saw. They never split an oversized request, never reorder
 * anything, and never repair a disagreement.
 *
 * Logs go to stderr only; stdout carries protocol frames exclusively.
 */

'use strict';

const mineflayer = require('mineflayer');
const vec3 = require('vec3');

const REACH = 4.5; // vanilla survival interaction range, in blocks
const MAX_REGION_BLOCKS = 32768;
const DEFAULT_TIMEOUT_MS = 20000;
const AIR = new Set(['air', 'cave_air', 'void_air']);
// Neighbour scan order used only when the caller does not name a face. Fixed
// and documented so a run is reproducible; override it with `face`.
const FACE_SCAN = [[0, -1, 0], [0, 1, 0], [-1, 0, 0], [1, 0, 0], [0, 0, -1], [0, 0, 1]].map((a) => vec3(...a));

// Vanilla /fill refuses more than this many blocks. The bridge refuses too,
// with the numbers attached: splitting a too-large region into pieces would be
// choosing a build order, which is the thing the cards measure.
const FILL_VOLUME_LIMIT = 32768;
const FILL_MODES = new Set(['replace', 'destroy', 'keep', 'outline', 'hollow']);
// The server reads a command's text with a 256-character cap and drops the
// connection past it, so an over-long command is refused here instead.
const MAX_COMMAND_CHARS = 256;
const CONFIRM_TIMEOUT_MS = 2000; // how long the single confirming read waits
const CONFIRM_POLL_MS = 50;
// A single unquoted command token: `stone_bricks`, `minecraft:oak_log`.
const COMMAND_TOKEN = /^[A-Za-z0-9_:./-]+$/;
// Control characters and the section sign get a client kicked for "illegal
// characters in chat"; a newline would also smuggle a second command through.
// The space is refused with them: no vanilla block state contains one, and a
// stray space would end the block argument, handing whatever follows to the
// command as its next argument.
const ILLEGAL_IN_COMMAND = /[\u0000-\u0020\u007f\u00a7]/;

let bot = null; // exactly one bot per bridge process
// Latest `declare_commands` packet: the server's command tree, filtered by
// this player's permission level and re-sent whenever that level changes.
// A vanilla server only lists `setblock`/`fill` for an operator, which is how
// "the server ignored my command because I am not op" can be told apart from
// "the command ran and the result disagrees with what I asked for".
let commandTree = null;

class BridgeError extends Error {
  constructor(code, message, detail = {}) {
    super(message);
    this.code = code;
    this.detail = detail;
  }
}

const log = (...a) => process.stderr.write(`[mc_bridge] ${a.join(' ')}\n`);

function withTimeout(promise, ms, code, what) {
  let timer;
  const guard = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new BridgeError(code, `${what} timed out after ${ms} ms`, { timeout_ms: ms })), ms);
  });
  return Promise.race([promise, guard]).finally(() => clearTimeout(timer));
}

function requireBot() {
  if (!bot || !bot.entity) throw new BridgeError('NOT_CONNECTED', 'No bot is connected; call connect first');
  return bot;
}

const asPos = (p) => ({ x: p.x, y: p.y, z: p.z });

function distanceToBlock(b, x, y, z) {
  return b.entity.position.offset(0, b.entity.height * 0.5, 0).distanceTo(vec3(x + 0.5, y + 0.5, z + 0.5));
}

// Public accessor since prismarine-block 1.14; fall back for older installs.
// Never reach into the private `_properties` field.
function blockProperties(blk) {
  return typeof blk.getProperties === 'function' ? blk.getProperties() : {};
}

/** {x,y,z} unit axis vector, or null when absent. */
function parseFace(o, what) {
  if (o === undefined || o === null) return null;
  const { x, y, z } = o;
  if (![x, y, z].every(Number.isInteger)) throw new BridgeError('BAD_PARAMS', `${what} must be {x,y,z} integers`);
  if (Math.abs(x) + Math.abs(y) + Math.abs(z) !== 1) {
    throw new BridgeError('BAD_PARAMS', `${what} must be a unit axis vector such as {"x":0,"y":1,"z":0}, got ${x},${y},${z}`);
  }
  return vec3(x, y, z);
}

/** {x,y,z} world point, or `fallback` when absent. */
function parsePoint(o, what, fallback) {
  if (o === undefined || o === null) return fallback;
  const { x, y, z } = o;
  if (![x, y, z].every((v) => typeof v === 'number' && Number.isFinite(v))) {
    throw new BridgeError('BAD_PARAMS', `${what} must be {x,y,z} finite numbers`);
  }
  return vec3(x, y, z);
}

function inventorySnapshot(b) {
  return b.inventory.items().map((i) => ({ name: i.name, count: i.count, slot: i.slot }));
}

/**
 * The client-side inventory lags the server by a tick or two after a place or
 * a withdraw, so reading it immediately reports stale counts. Wait until no
 * slot has changed for `quietMs`, capped at `maxMs`. Transport-level
 * synchronisation of a single call -- it does not retry anything.
 * Resolves true if the inventory went quiet, false if the cap was hit.
 */
function settleInventory(b, quietMs = 300, maxMs = 2000) {
  return new Promise((resolve) => {
    let quiet, hardStop, done = false;
    const finish = (settled) => {
      if (done) return;
      done = true;
      clearTimeout(quiet);
      clearTimeout(hardStop);
      b.inventory.removeListener('updateSlot', bump);
      resolve(settled);
    };
    const bump = () => { clearTimeout(quiet); quiet = setTimeout(() => finish(true), quietMs); };
    b.inventory.on('updateSlot', bump);
    quiet = setTimeout(() => finish(true), quietMs);
    hardStop = setTimeout(() => finish(false), maxMs);
  });
}

// ------------------------------------------------- server-command plumbing

/**
 * Does the server's command tree offer this top-level command to this bot?
 * true / false / null when no tree has been seen. Read-only: the bridge never
 * asks for op and never changes anyone's permission level.
 */
function serverOffersCommand(literal) {
  if (!commandTree || !Array.isArray(commandTree.nodes)) return null;
  const root = commandTree.nodes[commandTree.rootIndex];
  if (!root || !Array.isArray(root.children)) return null;
  return root.children.some((i) => {
    const node = commandTree.nodes[i];
    return !!(node && node.extraNodeData && node.extraNodeData.name === literal);
  });
}

/** A single bare command token, rejected rather than quoted or repaired. */
function commandToken(v, what) {
  if (typeof v !== 'string' || v.length === 0) throw new BridgeError('BAD_PARAMS', `${what} is required`);
  if (!COMMAND_TOKEN.test(v)) {
    throw new BridgeError('BAD_PARAMS', `${what} must be one bare command token such as "stone_bricks" or "minecraft:oak_log"`, { value: v });
  }
  return v;
}

/**
 * The caller's block state, character for character, inside the brackets the
 * command syntax needs. `axis=y` and `[axis=y]` both become `[axis=y]`; the
 * text between the brackets is never edited, reordered or filled in, because
 * the cards grade axis and facing.
 */
function bracketedState(s, what) {
  if (s === undefined || s === null || s === '') return '';
  if (typeof s !== 'string') throw new BridgeError('BAD_PARAMS', `${what} must be a string such as "axis=y" or "facing=north"`, { value: s });
  if (ILLEGAL_IN_COMMAND.test(s)) {
    throw new BridgeError('BAD_PARAMS', `${what} contains a space, a control character or a section sign, which the server refuses`, { value: s });
  }
  return s.startsWith('[') && s.endsWith(']') ? s : `[${s}]`;
}

/**
 * `[axis=y,half=top]` -> {axis: "y", half: "top"}, or null when the string is
 * not a plain list of key=value pairs. null means "not understood", and an
 * unread state is reported as unchecked rather than as agreeing.
 */
function statePairs(bracketed) {
  if (!bracketed) return {};
  const inner = bracketed.slice(1, -1);
  if (inner.trim() === '') return {};
  const pairs = {};
  for (const part of inner.split(',')) {
    const eq = part.indexOf('=');
    if (eq < 0) return null;
    const key = part.slice(0, eq).trim();
    const value = part.slice(eq + 1).trim();
    if (!key || !value) return null;
    pairs[key] = value;
  }
  return pairs;
}

const bareName = (n) => (typeof n === 'string' ? n.replace(/^minecraft:/, '') : n);

function cellSnapshot(b, pos) {
  const blk = b.blockAt(pos);
  if (!blk) return { x: pos.x, y: pos.y, z: pos.z, name: null, loaded: false };
  return { x: pos.x, y: pos.y, z: pos.z, name: blk.name, loaded: true, properties: blockProperties(blk) };
}

function sameCell(a, c) {
  if (a.name !== c.name || a.loaded !== c.loaded) return false;
  const pa = a.properties || {};
  const pc = c.properties || {};
  const keys = new Set([...Object.keys(pa), ...Object.keys(pc)]);
  for (const k of keys) if (String(pa[k]) !== String(pc[k])) return false;
  return true;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * One confirming read of one cell, polled until the server's update lands or
 * the deadline passes. It re-reads; it never re-sends. Whatever it last saw is
 * what gets reported, agreeing or not.
 */
async function confirmCell(b, pos, matches, timeoutMs) {
  const started = Date.now();
  let observed = cellSnapshot(b, pos);
  while (!matches(observed) && Date.now() - started < timeoutMs) {
    await sleep(CONFIRM_POLL_MS);
    observed = cellSnapshot(b, pos);
  }
  return { observed, matched: matches(observed), waited_ms: Date.now() - started };
}

/** Hand one command to the server, exactly once. */
function sendCommand(b, text) {
  const payload = text.slice(1); // the wire carries the command without its slash
  if (payload.length > MAX_COMMAND_CHARS) {
    throw new BridgeError('COMMAND_TOO_LONG', `command is ${payload.length} characters, the server accepts ${MAX_COMMAND_CHARS}`,
      { length: payload.length, limit: MAX_COMMAND_CHARS, command: text });
  }
  b.chat(text);
  return text;
}

// ---------------------------------------------------------------- primitives

async function connect(p) {
  if (bot) throw new BridgeError('ALREADY_CONNECTED', 'A bot is already connected on this bridge process', { username: bot.username });
  const { host = '127.0.0.1', port = 25565, username, version = '1.19.2', timeout_ms = 60000 } = p || {};
  if (!username) throw new BridgeError('BAD_PARAMS', 'username is required');

  // Offline-mode only, on purpose: the bridge never reads, prompts for or
  // accepts account credentials of any kind. It talks to unauthenticated test
  // servers (the cards' pinned compose file sets ONLINE_MODE=FALSE) and
  // defaults to 127.0.0.1.
  const pending = mineflayer.createBot({ host, port, username, version, auth: 'offline' });
  // A bot with no 'error' listener turns any late socket error into an
  // unhandled EventEmitter error, which would kill the whole bridge process.
  // Attach a durable listener before anything can fire; the once-listeners
  // below settle the connect call and are consumed by it.
  pending.on('error', (e) => log('bot error:', e && e.message ? e.message : e));
  bot = pending;
  commandTree = null;

  try {
    // The command tree arrives right after join and again on every permission
    // change, so listen before spawn and keep only the latest. `_client` is
    // mineflayer's raw protocol client; this reads a packet, it never sends one.
    // The `bot === pending` guard stops a late packet from a replaced connection
    // overwriting the tree of the bot that replaced it. Attached inside the try
    // so that anything thrown here still runs the quit-and-clear path below
    // rather than orphaning a live connection no one holds a handle to.
    pending._client.on('declare_commands', (packet) => { if (bot === pending) commandTree = packet; });
    await withTimeout(new Promise((resolve, reject) => {
      pending.once('spawn', resolve);
      pending.once('error', (e) => reject(new BridgeError('CONNECT_FAILED', String(e && e.message ? e.message : e))));
      pending.once('kicked', (r) => reject(new BridgeError('KICKED', typeof r === 'string' ? r : JSON.stringify(r))));
      pending.once('end', (r) => reject(new BridgeError('CONNECT_FAILED', `connection ended before spawn: ${r}`)));
    }), timeout_ms, 'CONNECT_TIMEOUT', 'spawn');
    await withTimeout(pending.waitForChunksToLoad(), timeout_ms, 'CHUNK_LOAD_TIMEOUT', 'chunk load');
  } catch (e) {
    try { pending.quit(); } catch (_) { /* already down */ }
    bot = null;
    commandTree = null;
    throw e;
  }

  pending.on('kicked', (r) => log('kicked:', typeof r === 'string' ? r : JSON.stringify(r)));
  // Only clear the slot if this bot is still the one in it: a late 'end' from a
  // previous connection must not disconnect the bot that replaced it.
  pending.on('end', (r) => { log('connection ended:', r); if (bot === pending) { bot = null; commandTree = null; } });

  return {
    username: pending.username,
    version: pending.version,
    position: asPos(pending.entity.position),
    // Whether this bot may run /setblock and /fill at all. null = the server
    // has not sent a command tree the bridge could read.
    operator: serverOffersCommand('setblock'),
  };
}

async function disconnect() {
  if (!bot) return { disconnected: false, reason: 'no active connection' };
  const name = bot.username;
  bot.quit();
  bot = null;
  commandTree = null;
  return { disconnected: true, username: name };
}

async function get_position() {
  const b = requireBot();
  const e = b.entity;
  return {
    position: asPos(e.position),
    block_position: asPos(e.position.floored()),
    yaw: e.yaw, pitch: e.pitch, on_ground: e.onGround,
    dimension: b.game && b.game.dimension,
  };
}

async function get_inventory() {
  const b = requireBot();
  const settled = await settleInventory(b);
  return {
    items: inventorySnapshot(b),
    held: b.heldItem ? b.heldItem.name : null,
    empty_slots: b.inventory.emptySlotCount(),
    settled, // false => counts may still be a tick behind the server
  };
}

async function read_region(p) {
  const b = requireBot();
  const { x1, y1, z1, x2, y2, z2 } = p || {};
  for (const [k, v] of Object.entries({ x1, y1, z1, x2, y2, z2 })) {
    if (!Number.isInteger(v)) throw new BridgeError('BAD_PARAMS', `${k} must be an integer, got ${JSON.stringify(v)}`);
  }
  const lo = { x: Math.min(x1, x2), y: Math.min(y1, y2), z: Math.min(z1, z2) };
  const hi = { x: Math.max(x1, x2), y: Math.max(y1, y2), z: Math.max(z1, z2) };
  const count = (hi.x - lo.x + 1) * (hi.y - lo.y + 1) * (hi.z - lo.z + 1);
  if (count > MAX_REGION_BLOCKS) {
    throw new BridgeError('REGION_TOO_LARGE', `region holds ${count} blocks, limit is ${MAX_REGION_BLOCKS}`, { blocks: count, limit: MAX_REGION_BLOCKS });
  }

  const blocks = [];
  let unloaded = 0;
  for (let x = lo.x; x <= hi.x; x++) {
    for (let y = lo.y; y <= hi.y; y++) {
      for (let z = lo.z; z <= hi.z; z++) {
        const blk = b.blockAt(vec3(x, y, z));
        if (!blk) { unloaded++; blocks.push({ x, y, z, name: null, loaded: false }); continue; }
        const entry = { x, y, z, name: blk.name, loaded: true };
        // Raw block state passthrough: facing/axis live here. No interpretation.
        const props = blockProperties(blk);
        if (props && Object.keys(props).length) entry.properties = props;
        blocks.push(entry);
      }
    }
  }
  return { min: lo, max: hi, count, unloaded, blocks };
}

async function place_block(p) {
  const b = requireBot();
  const { x, y, z, blockName, timeout_ms = DEFAULT_TIMEOUT_MS } = p || {};
  if (![x, y, z].every(Number.isInteger)) throw new BridgeError('BAD_PARAMS', 'x, y and z must be integers');
  if (!blockName) throw new BridgeError('BAD_PARAMS', 'blockName is required');

  const target = vec3(x, y, z);
  // The clicked face and the look vector are what the server derives a
  // directional block's `axis`/`facing`/`half` from, and the cards grade those.
  // So they are the caller's to set. The scan below is a documented default for
  // blocks whose state does not depend on them, not the bridge having a view.
  const wantFace = parseFace(p && p.face, 'face');
  const lookPoint = parsePoint(p && p.look, 'look', target.offset(0.5, 0.5, 0.5));
  const occupant = b.blockAt(target);
  if (!occupant) throw new BridgeError('CHUNK_NOT_LOADED', `target ${x},${y},${z} is not in a loaded chunk`);
  if (!AIR.has(occupant.name)) {
    throw new BridgeError('TARGET_OCCUPIED', `target ${x},${y},${z} already holds ${occupant.name}`, { observed: occupant.name });
  }

  const dist = distanceToBlock(b, x, y, z);
  if (dist > REACH) {
    throw new BridgeError('OUT_OF_REACH', `target is ${dist.toFixed(2)} blocks away, reach is ${REACH}`,
      { distance: dist, reach: REACH, bot_position: asPos(b.entity.position) });
  }

  const item = b.inventory.items().find((i) => i.name === blockName);
  if (!item) {
    throw new BridgeError('ITEM_NOT_IN_INVENTORY', `no ${blockName} in inventory`, { requested: blockName, inventory: inventorySnapshot(b) });
  }

  // A placement needs a solid neighbour to click on. `reference + face == target`.
  let reference = null, face = null, faceSource = 'auto';
  if (wantFace) {
    const refPos = target.minus(wantFace);
    const cand = b.blockAt(refPos);
    if (!cand || cand.boundingBox !== 'block') {
      throw new BridgeError('NO_ADJACENT_SUPPORT',
        `requested face ${wantFace.x},${wantFace.y},${wantFace.z} has no solid block to place against`,
        { requested_face: asPos(wantFace), reference: asPos(refPos), reference_block: cand ? cand.name : null });
    }
    reference = cand; face = wantFace; faceSource = 'caller';
  } else {
    for (const off of FACE_SCAN) {
      const cand = b.blockAt(target.plus(off));
      if (cand && cand.boundingBox === 'block') { reference = cand; face = off.scaled(-1); break; }
    }
    if (!reference) {
      throw new BridgeError('NO_ADJACENT_SUPPORT', `no solid block adjacent to ${x},${y},${z} to place against`,
        { neighbours: FACE_SCAN.map((o) => { const c = b.blockAt(target.plus(o)); return { offset: asPos(o), name: c ? c.name : null }; }) });
    }
  }

  if (!b.heldItem || b.heldItem.name !== blockName) {
    await withTimeout(b.equip(item, 'hand'), timeout_ms, 'EQUIP_TIMEOUT', `equip ${blockName}`);
  }
  await withTimeout(b.lookAt(lookPoint, true), timeout_ms, 'LOOK_TIMEOUT', 'lookAt');

  try {
    await withTimeout(b.placeBlock(reference, face), timeout_ms, 'PLACE_TIMEOUT', `place ${blockName}`);
  } catch (e) {
    if (e instanceof BridgeError) throw e;
    throw new BridgeError('PLACE_FAILED', String(e && e.message ? e.message : e),
      { reference: asPos(reference.position), reference_block: reference.name, face: asPos(face) });
  }

  const after = b.blockAt(target);
  const observed = after ? after.name : null;
  if (observed !== blockName) {
    throw new BridgeError('PLACED_MISMATCH', `server reports ${observed} at ${x},${y},${z}, expected ${blockName}`,
      { expected: blockName, observed });
  }
  return {
    placed: true, position: { x, y, z }, block: observed,
    properties: blockProperties(after),
    reference: asPos(reference.position), face: asPos(face), face_source: faceSource,
    look: asPos(lookPoint),
  };
}

/**
 * `/setblock` — the server's own placement command. No inventory, no reach, no
 * support block, but it needs operator permission. One command is sent, then
 * one confirming read reports what the world actually holds. A disagreement is
 * reported, never repaired.
 */
async function set_block(p) {
  const b = requireBot();
  const { x, y, z, blockName, blockState, confirm_timeout_ms = CONFIRM_TIMEOUT_MS } = p || {};
  if (![x, y, z].every(Number.isInteger)) throw new BridgeError('BAD_PARAMS', 'x, y and z must be integers');
  if (!Number.isInteger(confirm_timeout_ms) || confirm_timeout_ms < 0) {
    throw new BridgeError('BAD_PARAMS', 'confirm_timeout_ms must be a non-negative integer');
  }
  const name = commandToken(blockName, 'blockName');
  const state = bracketedState(blockState, 'blockState');
  const wanted = statePairs(state); // null => not a plain key=value list
  // Something to check against: a plain key=value list with at least one pair.
  // `""` and `"[]"` both ask for nothing, and are reported as checking nothing.
  const hasWanted = wanted !== null && Object.keys(wanted).length > 0;

  const target = vec3(x, y, z);
  const before = cellSnapshot(b, target);
  const sent = sendCommand(b, `/setblock ${x} ${y} ${z} ${name}${state}`);

  const stateHolds = (cell) => wanted === null || Object.entries(wanted).every(([k, v]) => String((cell.properties || {})[k]) === v);
  const matches = (cell) => cell.loaded && bareName(cell.name) === bareName(name) && stateHolds(cell);

  let observed = before;
  let matched = false;
  let waited = 0;
  // A cell outside the client's loaded view never reports back, so there is
  // nothing to wait for. /setblock still reaches it; the bridge just says so.
  if (before.loaded) ({ observed, matched, waited_ms: waited } = await confirmCell(b, target, matches, confirm_timeout_ms));

  const verified = before.loaded ? matched : null;
  const operator = serverOffersCommand('setblock');
  const result = {
    sent,
    position: { x, y, z },
    block: name,
    block_state: blockState === undefined ? null : blockState,
    verified,
    changed: !sameCell(before, observed),
    state_checked: hasWanted,
    state_match: !hasWanted || !observed.loaded ? null : stateHolds(observed),
    before,
    observed,
    operator,
    waited_ms: waited,
  };
  if (verified === null) result.unverified_reason = 'target is not in a chunk this client has loaded';

  // The cell changed into what was asked for: the command demonstrably ran.
  if (verified === true && result.changed) return result;
  if (operator === false) {
    throw new BridgeError('NOT_OPERATOR',
      `the server offers no "setblock" command to ${b.username}, so ${sent} was ignored; /setblock needs operator permission`,
      { ...result, command: sent });
  }
  if (verified === true) return result; // already held it; nothing moved
  if (verified === null) return result; // out of view, honestly unverified
  throw new BridgeError('PLACED_MISMATCH',
    `server reports ${observed.name} at ${x},${y},${z} after ${sent}, expected ${name}${state}`,
    { ...result, expected: `${name}${state}` });
}

/**
 * `/fill` — the server's own bulk placement command, subject to the same
 * operator permission. Over the vanilla volume limit it is refused with the
 * numbers attached rather than split into pieces: choosing how to break a
 * region into batches is a build plan, and build plans are what the cards
 * score. Nothing is reordered and nothing is retried.
 *
 * The confirming read looks at one cell, the corner named by x1,y1,z1. Which
 * blocks inside the region actually changed is a `read_region` away, and
 * deciding what to make of that difference stays with the caller.
 */
async function fill_region(p) {
  const b = requireBot();
  const { x1, y1, z1, x2, y2, z2, blockName, mode = 'replace', confirm_timeout_ms = CONFIRM_TIMEOUT_MS } = p || {};
  for (const [k, v] of Object.entries({ x1, y1, z1, x2, y2, z2 })) {
    if (!Number.isInteger(v)) throw new BridgeError('BAD_PARAMS', `${k} must be an integer, got ${JSON.stringify(v)}`);
  }
  if (!Number.isInteger(confirm_timeout_ms) || confirm_timeout_ms < 0) {
    throw new BridgeError('BAD_PARAMS', 'confirm_timeout_ms must be a non-negative integer');
  }
  const name = commandToken(blockName, 'blockName');
  if (typeof mode !== 'string' || !FILL_MODES.has(mode)) {
    throw new BridgeError('BAD_PARAMS', `mode must be one of ${[...FILL_MODES].join(', ')}`, { mode, allowed: [...FILL_MODES] });
  }

  const min = { x: Math.min(x1, x2), y: Math.min(y1, y2), z: Math.min(z1, z2) };
  const max = { x: Math.max(x1, x2), y: Math.max(y1, y2), z: Math.max(z1, z2) };
  const volume = (max.x - min.x + 1) * (max.y - min.y + 1) * (max.z - min.z + 1);
  if (volume > FILL_VOLUME_LIMIT) {
    throw new BridgeError('FILL_VOLUME_EXCEEDED',
      `region holds ${volume} blocks, /fill accepts ${FILL_VOLUME_LIMIT}; the bridge does not split a region for you`,
      { volume, limit: FILL_VOLUME_LIMIT, min, max });
  }

  const probePos = vec3(x1, y1, z1);
  const before = cellSnapshot(b, probePos);
  const sent = sendCommand(b, `/fill ${x1} ${y1} ${z1} ${x2} ${y2} ${z2} ${name} ${mode}`);

  const matches = (cell) => cell.loaded && bareName(cell.name) === bareName(name);
  let observed = before;
  let matched = false;
  let waited = 0;
  if (before.loaded) ({ observed, matched, waited_ms: waited } = await confirmCell(b, probePos, matches, confirm_timeout_ms));

  const verified = before.loaded ? matched : null;
  const operator = serverOffersCommand('fill');
  // `keep` only touches air, so the probe corner staying as it was proves
  // nothing either way. Every other mode always writes the corner.
  const probeConclusive = mode !== 'keep';
  const result = {
    sent,
    min,
    max,
    volume,
    limit: FILL_VOLUME_LIMIT,
    mode,
    block: name,
    verified,
    changed: !sameCell(before, observed),
    probe_position: { x: x1, y: y1, z: z1 },
    probe_conclusive: probeConclusive,
    before,
    observed,
    operator,
    waited_ms: waited,
  };
  if (verified === null) result.unverified_reason = 'probe corner is not in a chunk this client has loaded';

  if (verified === true && result.changed) return result;
  if (operator === false) {
    throw new BridgeError('NOT_OPERATOR',
      `the server offers no "fill" command to ${b.username}, so ${sent} was ignored; /fill needs operator permission`,
      { ...result, command: sent });
  }
  if (verified === true) return result;
  if (verified === null) return result;
  if (!probeConclusive) return result; // keep mode: the corner tells us nothing
  throw new BridgeError('PLACED_MISMATCH',
    `server reports ${observed.name} at the probe corner ${x1},${y1},${z1} after ${sent}, expected ${name}`,
    { ...result, expected: name });
}

async function withdraw_from_chest(p) {
  const b = requireBot();
  const { x, y, z, itemName, count, timeout_ms = DEFAULT_TIMEOUT_MS } = p || {};
  if (![x, y, z].every(Number.isInteger)) throw new BridgeError('BAD_PARAMS', 'x, y and z must be integers');
  if (!itemName) throw new BridgeError('BAD_PARAMS', 'itemName is required');
  if (!Number.isInteger(count) || count <= 0) throw new BridgeError('BAD_PARAMS', 'count must be a positive integer');

  const block = b.blockAt(vec3(x, y, z));
  if (!block) throw new BridgeError('CHUNK_NOT_LOADED', `chest position ${x},${y},${z} is not in a loaded chunk`);

  const dist = distanceToBlock(b, x, y, z);
  if (dist > REACH) {
    throw new BridgeError('OUT_OF_REACH', `container is ${dist.toFixed(2)} blocks away, reach is ${REACH}`,
      { distance: dist, reach: REACH, bot_position: asPos(b.entity.position) });
  }

  const def = b.registry.itemsByName[itemName];
  if (!def) throw new BridgeError('UNKNOWN_ITEM', `no item named ${itemName} in the ${b.version} registry`, { item: itemName });

  // Measure before opening: while a container window is open the player's
  // slots belong to that window, so bot.inventory does not move until it closes.
  await settleInventory(b);
  const before = b.inventory.count(def.id, null);

  let container;
  try {
    container = await withTimeout(b.openContainer(block), timeout_ms, 'OPEN_TIMEOUT', `open ${block.name}`);
  } catch (e) {
    if (e instanceof BridgeError) throw e;
    throw new BridgeError('CONTAINER_OPEN_FAILED', String(e && e.message ? e.message : e), { observed: block.name });
  }

  let closed = false;
  try {
    const contents = container.containerItems().map((i) => ({ name: i.name, count: i.count }));
    const total = contents.filter((i) => i.name === itemName).reduce((s, i) => s + i.count, 0);
    if (total < count) {
      throw new BridgeError('INSUFFICIENT_STOCK', `chest holds ${total} ${itemName}, requested ${count}`,
        { requested: count, available: total, contents });
    }
    await withTimeout(container.withdraw(def.id, null, count), timeout_ms, 'WITHDRAW_TIMEOUT', `withdraw ${itemName}`);
    container.close();
    closed = true;
    const settled = await settleInventory(b);
    const after = b.inventory.count(def.id, null);
    return { withdrawn: after - before, item: itemName, requested: count, inventory_count: after, settled };
  } catch (e) {
    if (e instanceof BridgeError) throw e;
    throw new BridgeError('WITHDRAW_FAILED', String(e && e.message ? e.message : e), { item: itemName, requested: count });
  } finally {
    if (!closed) try { container.close(); } catch (_) { /* window already gone */ }
  }
}

// ---------------------------------------------------------------- rpc plumbing

const METHODS = {
  connect, disconnect, get_position, get_inventory, read_region,
  place_block, set_block, fill_region, withdraw_from_chest,
};

function send(frame) {
  try {
    process.stdout.write(`${JSON.stringify(frame)}\n`);
  } catch (e) {
    // Nobody is listening any more; say so on stderr and go down cleanly
    // rather than wedging the request queue.
    log('stdout write failed:', e && e.message ? e.message : e);
    shutdown(0);
  }
}

/**
 * Drop the connection and leave. `exitCode` alone lets the loop drain pending
 * stdout writes and the socket teardown; the unref'd timer is the backstop for
 * a handle that refuses to close, so the process can never linger as a zombie
 * holding a live bot session.
 */
let shuttingDown = false;
function shutdown(code) {
  if (shuttingDown) return;
  shuttingDown = true;
  if (bot) { try { bot.quit(); } catch (_) { /* already down */ } bot = null; }
  process.exitCode = code;
  setTimeout(() => process.exit(code), 500).unref();
}

async function dispatch(line) {
  let req;
  try {
    req = JSON.parse(line);
  } catch (e) {
    return send({ id: null, ok: false, error: { code: 'BAD_JSON', message: String(e.message), detail: { line: line.slice(0, 200) } } });
  }
  const id = req.id === undefined ? null : req.id;
  const fn = METHODS[req.method];
  if (!fn) {
    return send({ id, ok: false, error: { code: 'UNKNOWN_METHOD', message: `no such method: ${req.method}`, detail: { known: Object.keys(METHODS) } } });
  }
  try {
    send({ id, ok: true, result: await fn(req.params || {}) });
  } catch (e) {
    const err = e instanceof BridgeError
      ? { code: e.code, message: e.message, detail: e.detail }
      : { code: 'INTERNAL_ERROR', message: String(e && e.message ? e.message : e), detail: { stack: e && e.stack ? e.stack.split('\n').slice(0, 4) : [] } };
    send({ id, ok: false, error: err });
  }
}

// Requests are serialised: one world action at a time, in arrival order.
// The chain is kept un-rejectable: one rejected link would silently swallow
// every later request and stop the process from ever exiting.
let queue = Promise.resolve();
let buffer = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
  buffer += chunk;
  let nl;
  while ((nl = buffer.indexOf('\n')) >= 0) {
    const line = buffer.slice(0, nl).trim();
    buffer = buffer.slice(nl + 1);
    if (line) queue = queue.then(() => dispatch(line)).catch((e) => log('dispatch failed:', e && e.message ? e.message : e));
  }
});

// Every way this process can be asked to stop ends in the same cleanup.
process.stdin.on('end', () => { queue.then(() => shutdown(0), () => shutdown(0)); });
process.stdout.on('error', (e) => { log('stdout error:', e && e.code ? e.code : e); shutdown(0); });
for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(sig, () => { log(`${sig}: shutting down`); shutdown(0); });

log('ready');
