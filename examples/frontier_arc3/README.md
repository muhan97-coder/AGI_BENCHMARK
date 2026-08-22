# frontier_arc3 — setup and agent-loop skeleton

This is **not** a teaching demo in the shape of the other twelve
`examples/<category>/` directories: there is no `card.json`, no `solution/`,
no offline RED → GREEN walkthrough. `frontier_arc3` grades a live session
against the real ARC Prize server (`https://three.arcprize.org`), so a
faithful offline reproduction does not exist — mocking the server would teach
you the mock, not the grading contract. What follows is the setup and the
loop shape instead: get this working once, and every `frontier_arc3` card
(`cards/gc-464_*.json` .. `cards/gc-475_*.json`) uses the same shape at a
different level/game bar.

## 1. Provenance note: why only 3 confirmed games

Every `frontier_arc3` card seals its `assets/gc-4NN/game_ids.txt` allowlist
to a subset of exactly three game codes: **`ls20`** ("LS20", agent
reasoning), **`ft09`** ("FT09", elementary logic), **`vc33`** ("VC33",
orchestration). This investigation (2026-08-22) could confirm those three
against official ARC Prize sources and no others:

- `https://docs.arcprize.org/available-games` names exactly these three as
  the games accessible to an anonymous (unregistered) API key.
- The OpenAPI spec (`https://docs.arcprize.org/arc3v1.yaml`) embeds a
  `GET /api/games` response example listing `ls20-016295f7601e` ("LS20") and
  `ft09-16726c5b26ff` ("FT09") verbatim.

A **community mirror repo** (`github.com/axobase001/arc-agi-games`, not an
`arcprize` org repo) lists ~25 game ids, and the official benchmarking
harness (`github.com/arcprize/arc-agi-3-benchmarking`) tells its own README
reader to expect "there should be 25" via a `--list-games` CLI flag whose
actual output this investigation did not capture. Neither source is an
ARC-Prize-published static list, so this repository does not seal a card
against ids it cannot independently verify are real — sealing against a
guessed or unverified id risks a card nobody can ever pass (the game might
not exist) or, worse, a card that silently accepts whatever a live
`/api/games` call happens to return that day, which is the opposite of a
sealed, reproducible card.

**If you have a registered API key**, run this once and compare against the
three above before trusting a wider set for your own work:

```sh
curl -s -H "X-API-Key: $ARC_API_KEY" https://three.arcprize.org/api/games | python3 -m json.tool
```

That live call is the actual source of truth for "what games exist today" —
these cards intentionally do not hardcode more than what official docs
already state, and `grade.py` never trusts a static id list for anything
beyond the sealed allowlist check (levels, scores, and win state are always
read live from the scorecard, never assumed).

## 2. Get an API key

1. Go to `https://arcprize.org/platform` and sign in (Google or GitHub).
2. Open your profile → **API Keys** → create an `ARC_AGI_API` key.
3. Export it in your shell — **never commit it, never print it to a log
   graders or CI might capture**:

   ```sh
   export ARC_API_KEY="<your key>"
   ```

`assets/gc-4NN/grade.py` in every `frontier_arc3` card reads this exact
environment variable and never writes its value anywhere.

## 3. Install the toolkit (optional convenience)

```sh
pip install arc-agi==0.9.9
```

This pins the version this band's cards were authored against
(`https://pypi.org/project/arc-agi/0.9.9/`; PyPI's latest at authoring time —
re-check before you rely on it, the toolkit ships fast). It is a convenience
for driving `RESET`/`ACTION` calls with a typed client; **the grader itself
never imports it** — `grade.py` is stdlib-only REST calls, by design, so
grading never depends on a third-party package's correctness.

Without the package, plain `urllib`/`requests` against the REST endpoints
below works identically; the toolkit just saves you writing the HTTP glue.

## 4. Agent-loop skeleton

Every `frontier_arc3` card follows the same shape. This sketch targets
`gc-464` (win 1 level of `ls20`) — swap the game code and the win condition
for a different card, the mechanics do not change:

```python
import json
import os
import urllib.request

BASE = "https://three.arcprize.org"
API_KEY = os.environ["ARC_API_KEY"]
CARD = "gc-464"


def call(method, path, body=None):
    req = urllib.request.Request(
        f"{BASE}{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


# 1. open a scorecard for this attempt
scorecard = call("POST", "/api/scorecard/open", {"tags": [CARD]})
card_id = scorecard["card_id"]

# 2. resolve the sealed game code (assets/gc-464/game_ids.txt) to a live
#    game_id via GET /api/games -- never hardcode the hash suffix, it can
#    change between sessions.
games = call("GET", "/api/games")
game_id = next(g["game_id"] for g in games if g["game_id"].startswith("ls20-"))

# 3. RESET starts (or restarts) a session; the response carries a `guid`
#    that every subsequent ACTION call must echo back.
frame = call("POST", "/api/cmd/RESET", {"game_id": game_id, "card_id": card_id})
guid = frame["guid"]

# 4. drive the game: read frame["frame"] (a 64x64 grid, 4-bit color per
#    cell), pick from frame["available_actions"], call the matching
#    ACTION1..ACTION7 endpoint, and repeat until frame["state"] is WIN or
#    GAME_OVER. ACTION6 additionally needs x, y in [0, 63].
while frame["state"] == "NOT_FINISHED":
    action_id = choose_action(frame)  # your policy goes here
    body = {"game_id": game_id, "guid": guid}
    if action_id == 6:
        body["x"], body["y"] = choose_xy(frame)
    frame = call("POST", f"/api/cmd/ACTION{action_id}", body)

# 5. close the scorecard -- the grader reads THIS closed record, not
#    anything in this process's memory.
call("POST", "/api/scorecard/close", {"card_id": card_id})

# 6. hand the scorecard id to the grader.
os.makedirs(f"runs/{CARD}", exist_ok=True)
with open(f"runs/{CARD}/scorecard_id.txt", "w") as fh:
    fh.write(card_id + "\n")
```

Then grade it:

```sh
python3 cards/assets/gc-464/grade.py
```

The last stdout line is the JSON verdict, e.g. `{"levels_won": 1}` —
`tools/goal_grader.py` reads that key against the card's
`success_criteria.spec` the same way it reads every other card's grader
output.

## 5. What differs by card

- **Metric name** varies with what the card asks for: `levels_won` (smoke,
  single-game progression), `games_at_min` (breadth, capstone-depth), or
  `score_pct` (efficiency/transfer — a percentage derived from the server's
  own RHAE `score` field, see `https://docs.arcprize.org/methodology`; a
  weak game caps the whole card, see each card's `goal`).
- **Sealed games** vary — check `cards/assets/gc-4NN/game_ids.txt` for the
  exact allowlist; `grade.py` fails the whole scorecard closed if any
  environment it reports carries a game id outside that list, so open one
  scorecard per card, not a shared one across cards.
- **Rate limit**: 600 requests/min (`https://docs.arcprize.org/rate_limits`).
  Interactive step cost is real: unlike the static `frontier_arc` grid
  cards, every `RESET`/`ACTION` call is a turn against a live session, so
  plan your action budget, not just your token budget.

## 6. Verifying without a live key

If you do not have `ARC_API_KEY` set, every `grade.py` in this band fails
closed to `{"<metric>": 0}` immediately and says so on stderr — that is the
intended behavior, not a bug to work around. The repository's own
verification of this band mocked the scorecard response locally (fail-closed
path unit checks: missing key, missing scorecard id, HTTP 401, malformed
body, a game id outside the seal, and the success path for each of the three
scoring modes) rather than skipping validation outright; it did not perform a
real network smoke test, since no key was available in that environment
either. Do the same before you trust a new `grade.py` change: mock
`urllib.request.urlopen`, do not assume.

## Grading integrity (read before scoring anyone)

Grade in a **fresh maintainer-side workspace** re-assembled from the repo's
canonical `cards/assets/` — copy only the agent's `runs/gc-4NN/` output in.
Running `tools/goal_grader.py` against the agent's own workspace lets the
agent overwrite its copy of `grade.py` / `game_ids.txt` and forge a PASS
(demonstrated live 2026-08-22, see CHANGELOG). Scorecard ids are server
receipts but are not yet bound to a session owner — treat a scorecard whose
opening you did not witness in the run ledger as unverified.
