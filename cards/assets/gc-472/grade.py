#!/usr/bin/env python3
"""Fail-closed grader for gc-472 (Transfer: carry LS20 efficiency tactics into 40% RHAE on FT09).

Reads the sealed game-id allowlist next to this script (game_ids.txt), reads
the scorecard id this attempt produced from runs/gc-472/scorecard_id.txt, and
does a live GET against the ARC-AGI-3 REST API to fetch that scorecard's
server-side record -- the verdict is what the ARC Prize server recorded an
agent doing, not anything the agent wrote to a local file. No LLM judgment,
no local forgery surface: predictions.json-style local files do not exist in
this card family on purpose (see project background in the card's resources).

Prediction contract: there is no local prediction file. The agent's "answer"
IS the play -- POST /api/scorecard/open, drive RESET + ACTION1..7 against the
sealed game(s) in game_ids.txt, POST /api/scorecard/close, then write the
returned card_id (first line, nothing else) to runs/gc-472/scorecard_id.txt
before running this grader.

Sealing: every environment the fetched scorecard reports must carry a game id
whose code (the part before the first "-") is in the sealed allowlist. A
scorecard that touched any game outside the allowlist fails closed to 0 --
open one scorecard per card, not a shared one.

Scoring mode = 'score_pct':
  gate: every allowed game's summed levels_completed must be >=
  GATE_MIN_LEVELS, else metric = 0. Otherwise metric = round(100 * the
  WORST per-game `score` among allowed games) -- `score` is the server's
  own RHAE-derived game_score (see methodology in this card's resources),
  so one weak game caps the whole card: this rewards efficiency that
  holds up across every game played, not one lucky run.

Missing/empty scorecard_id.txt, missing ARC_API_KEY, any network or HTTP
error, or a malformed/non-object response -> {"score_pct": 0} (fail
closed: nothing is certified without a live, well-formed server record). The
final stdout line is always the JSON verdict.
"""
import json
import os
import sys
import urllib.error
import urllib.request

CARD = "gc-472"
BASE_URL = "https://three.arcprize.org"
MODE = "score_pct"                  # one of: sum_levels | games_at_min | score_pct
GATE_MIN_LEVELS = 3         # per allowed game: levels_completed needed to "count"
METRIC_NAME = "score_pct"
HERE = os.path.dirname(os.path.abspath(__file__))
GAME_IDS_PATH = os.path.join(HERE, "game_ids.txt")
SCORECARD_ID_PATH = os.path.join("runs", CARD, "scorecard_id.txt")
MAX_RETRIES = 3


def note(msg):
    sys.stderr.write("[grade %s] %s\n" % (CARD, msg))


def finish(metric):
    print(json.dumps({METRIC_NAME: metric}))
    sys.exit(0)


def load_allowed_codes():
    with open(GAME_IDS_PATH) as fh:
        codes = [line.strip().lower() for line in fh if line.strip()]
    if not codes:
        raise RuntimeError("sealed game_ids.txt is empty")
    return codes


def load_scorecard_id():
    if not os.path.exists(SCORECARD_ID_PATH):
        raise RuntimeError("scorecard id file missing: %s" % SCORECARD_ID_PATH)
    with open(SCORECARD_ID_PATH) as fh:
        for line in fh:
            line = line.strip()
            if line:
                return line
    raise RuntimeError("scorecard id file is empty: %s" % SCORECARD_ID_PATH)


def fetch_scorecard(card_id, api_key):
    url = "%s/api/scorecard/%s" % (BASE_URL, card_id)
    req = urllib.request.Request(url, headers={"X-API-Key": api_key})
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            if err.code in (401, 403):
                raise RuntimeError("auth rejected by server (status %d) -- "
                                    "ARC_API_KEY is set but not accepted" % err.code)
            if err.code == 404:
                raise RuntimeError("scorecard %s not found (status 404)" % card_id)
            last_err = err
            if err.code != 429:
                break
        except Exception as err:  # transient network error: retry
            last_err = err
    raise RuntimeError("could not fetch scorecard %s: %r" % (card_id, last_err))


def as_num(value, cast, default):
    try:
        return cast(value)
    except (TypeError, ValueError):
        return default


def main():
    api_key = os.environ.get("ARC_API_KEY", "").strip()
    if not api_key:
        note("ARC_API_KEY is not set")
        finish(0)
    try:
        allowed = load_allowed_codes()
    except Exception as err:
        note("failed to read sealed game ids: %r" % err)
        finish(0)
    try:
        card_id = load_scorecard_id()
    except Exception as err:
        note(str(err))
        finish(0)
    try:
        scorecard = fetch_scorecard(card_id, api_key)
    except Exception as err:
        note(str(err))
        finish(0)
    if not isinstance(scorecard, dict):
        note("scorecard response is not a JSON object")
        finish(0)
    environments = scorecard.get("environments")
    if not isinstance(environments, list):
        note("scorecard response has no environments list")
        finish(0)

    levels_by_code = {code: 0 for code in allowed}
    score_by_code = {code: 0.0 for code in allowed}
    for env in environments:
        if not isinstance(env, dict):
            note("skipping malformed environment entry")
            finish(0)
        gid = env.get("id") or env.get("game_id") or env.get("game_code")
        if not gid:
            note("environment entry has no game id")
            finish(0)
        code = str(gid).split("-", 1)[0].lower()
        if code not in allowed:
            note("GAME_ID_NOT_SEALED: environment %r is not in game_ids.txt" % gid)
            finish(0)
        levels_by_code[code] += as_num(env.get("levels_completed", 0), int, 0)
        score_by_code[code] = max(score_by_code[code],
                                   as_num(env.get("score", 0.0), float, 0.0))

    for code in allowed:
        note("%s levels=%d score=%.3f" % (code, levels_by_code[code], score_by_code[code]))

    if MODE == "sum_levels":
        metric = sum(levels_by_code[c] for c in allowed)
    elif MODE == "games_at_min":
        metric = sum(1 for c in allowed if levels_by_code[c] >= GATE_MIN_LEVELS)
    elif MODE == "score_pct":
        if any(levels_by_code[c] < GATE_MIN_LEVELS for c in allowed):
            metric = 0
        else:
            metric = int(round(100 * min(score_by_code[c] for c in allowed)))
            metric = max(0, min(100, metric))
    else:
        note("unknown MODE %r" % MODE)
        metric = 0
    finish(metric)


if __name__ == "__main__":
    main()
