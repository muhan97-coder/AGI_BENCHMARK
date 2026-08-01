# Worked example — `infra_ops`

A **teaching example**, not a benchmark card. `card.json` here carries
`"scored": false` and its own reference solution ships in `solution/`. It exists
so you can watch an `infra_ops` card go RED → GREEN end to end before you point
an agent at the real ones.

| | scored cards (gc-372 … gc-383) | this example |
|---|---|---|
| runtime | docker + docker compose, pinned images | `assets/ex-infra_ops/minictl.py`, a sealed stdlib-only stand-in |
| services | nginx, redis, postgres, pgbouncer | `miniweb`, `minicache` (local processes on 127.0.0.1) |
| check | `bash assets/gc-372/check.sh` → `{"checks_passed": N, "checks_total": 6}` | `bash assets/ex-infra_ops/check.sh` → same JSON line, same 6 layers |
| wall time | minutes, several GB of images | **0.8 s**, no network, no docker |

Everything else is identical on purpose: the same layered healthcheck
(parse → pin → start → publish → HTTP contract → liveness), the same
"only files under `stack/` may be edited", the same sealed check you must not
touch.

---

## 0. Set up a workspace

Copy the task assets into a scratch workspace — never point an agent at this
repository, or the reference solution is one `cat` away.

```sh
WS="${TMPDIR:-/tmp}/ws-ex-infra_ops"
mkdir -p "$WS" && cp -a examples/infra_ops/assets "$WS"/
```

The card's spec is well-formed (this costs nothing and executes nothing):

```console
$ python3 tools/goal_grader.py --dry-run examples/infra_ops/card.json
{"card": "examples/infra_ops/card.json", "spec_ok": true, "problems": []}
```

## 1. Grade the unsolved workspace — RED, with a real metric

```console
$ python3 tools/goal_grader.py examples/infra_ops/card.json "$WS"
{
 "card_id": "ex-infra_ops",
 "grader": "script",
 "command": "bash assets/ex-infra_ops/check.sh",
 "wall_s": 0.5,
 "timed_out": false,
 "stdout_tail": "{\"checks_passed\": 1, \"checks_total\": 6}\n",
 "returncode": 0,
 "verdict": "FAIL",
 "passed": false,
 "metric_value": 1.0,
 "threshold": 6.0,
 "compare": ">="
}
```

Exit code `1`. This is the healthy starting state described in the root README:
**`FAIL` with a `metric_value` means the card works and the agent simply has not
done the work yet.** One of six checks passes — the stack file parses. Nothing
else does.

## 2. Diagnose layer by layer (what the agent is expected to do)

The metric alone (`1`) is useless for repair. The failure *identities* come from
the runtime's own diagnostics:

```console
$ python3 assets/ex-infra_ops/minictl.py --stack assets/ex-infra_ops/stack/stack.json config
services:
  cache:
    image: minicache:7.2.4-bogus
  web:
    image: miniweb:latest
    published: 8080->80
```

Two defects visible without starting anything: a floating `:latest` tag (that is
check C2) and a published host port of `8080` where the contract says `8391` (C4).

```console
$ python3 assets/ex-infra_ops/minictl.py --stack assets/ex-infra_ops/stack/stack.json conftest web
conftest web FAILED: line 2: directive 'listen 8080' is missing its terminating ';'
```

`conftest` is this example's `nginx -t`. Until the config parses, every other
diagnostic is noise — fix this first.

```console
$ python3 assets/ex-infra_ops/minictl.py --project dx --stack assets/ex-infra_ops/stack/stack.json up
service cache: image 'minicache:7.2.4-bogus' not found in the pinned local registry (available: minicache:7.2.4, miniweb:1.25.4)
service web: image 'miniweb:latest' not found in the pinned local registry (available: minicache:7.2.4, miniweb:1.25.4)
```

The dead tag stands in for an unpullable image. After pinning both images and
fixing `site.conf` (`listen 80;`, `root /usr/share/site;`) the *next* layer
becomes visible — a defect the first `up` could not have shown you:

```console
$ python3 assets/ex-infra_ops/minictl.py --project dx --stack assets/ex-infra_ops/stack/stack.json up
service web: no volume mounts the config root '/usr/share/site' (mounts: none)
cache: running (image minicache:7.2.4, published 57189->6379)

$ bash assets/ex-infra_ops/check.sh
{"checks_passed": 3, "checks_total": 6}
```

`1 → 3`. That midpoint is the point of the whole card: defects are **layered**,
so a plan that pattern-matches all five at once and edits blind cannot tell which
edit moved the number.

## 3. Apply the reference solution

```sh
sh examples/infra_ops/solution/apply.sh "$WS"
```

Two files, both under `stack/` — the sealed `check.sh` and `minictl.py` are never
touched:

- `stack/stack.json` — both images pinned to registry tags, `8391:80` published,
  `./html:/usr/share/site:ro` mounted.
- `stack/site.conf` — `listen 80;` (terminated, and matching the container port
  the stack publishes), `root /usr/share/site;` (matching the mount).

It also drops `work/repair_plan.md`, the plan artifact the card's
`process_expectations` demand *before* the first edit.

## 4. Grade again — GREEN

```console
$ python3 tools/goal_grader.py examples/infra_ops/card.json "$WS"
{
 "card_id": "ex-infra_ops",
 "grader": "script",
 "command": "bash assets/ex-infra_ops/check.sh",
 "wall_s": 0.8,
 "timed_out": false,
 "stdout_tail": "{\"checks_passed\": 6, \"checks_total\": 6}\n",
 "returncode": 0,
 "verdict": "PASS",
 "passed": true,
 "metric_value": 6.0,
 "threshold": 6.0,
 "compare": ">="
}
```

Exit code `0`.

---

## What the grader actually measured

`tools/goal_grader.py` ran one shell line, `bash assets/ex-infra_ops/check.sh`,
took the **last JSON line of its stdout**, read the key named by
`success_criteria.spec.metric` (`checks_passed`) and compared it to
`threshold: 6` with `compare: ">="`. That is the entire outcome axis — no LLM
judged anything.

The sealed check itself is six independent probes:

| check | what it proves | how it fails |
|---|---|---|
| C1 | the stack file parses | `config -q` exits non-zero |
| C2 | every image pinned | `:latest` appears in normalized output |
| C3 | both services reach `running` | `ps --status running --services` counts < 2 |
| C4 | the site is published on host port **8391** | `port web 80` prints nothing or the wrong port |
| C5 | HTTP 200 carrying the content token | an independent stdlib client cannot fetch `ex-infra-ops-stack-ok` |
| C6 | the cache is alive | `cache-cli ping` does not answer `PONG` |

Note C5's design: the token lives in the *shipped* `html/index.html`, which the
agent may not edit. You cannot satisfy it by writing the token somewhere
convenient — the stack has to actually mount and serve that directory. That is
what keeps the card from being gameable by a `stack.json` that merely *looks*
right.

## What good process would have looked like here

The outcome above (`6/6`) says nothing about *how* it was reached. The process
axes read the episode log (`episode.jsonl`, see the root README). For this card
a sound loop emits roughly this shape — **illustrative, not a captured run**:

```jsonl
{"event":"PLAN","plan_id":"p1","summary":"5 suspected defects, each with its confirming command; repair order conf -> images -> mount -> port","candidates_considered":5}
{"event":"VERIFY","target":"baseline","command":"bash assets/ex-infra_ops/check.sh","ran":true,"verdict":"RED","failed_ids":["C2 floating tag","C3 not running","C4 port 8080","C5 no content","C6 no cache"]}
{"event":"VERIFY","target":"D3 site.conf","command":"minictl conftest web","ran":true,"verdict":"RED","failed_ids":["site.conf:2 missing ';'"]}
{"event":"VERIFY","target":"after conf+images","command":"bash assets/ex-infra_ops/check.sh","ran":true,"verdict":"RED","failed_ids":["C4 port 8080","C5 no content"]}
{"event":"COST","usd":0.004,"purpose":"diagnose + repair"}
{"event":"VERIFY","target":"final","command":"bash assets/ex-infra_ops/check.sh","ran":true,"verdict":"GREEN","failed_ids":[]}
{"event":"HALT","reason":"goal_green"}
```

What each axis would pick up:

- **planning** — one `PLAN` naming five candidate defects *and the command that
  confirms each*, written before the first edit (`work/repair_plan.md` is its
  artifact). A plan that lists fixes but no confirmations scores lower.
- **verification** — four `VERIFY` events that actually `ran`, each carrying
  failure **identities** (`C4 port 8080`), not a count. The count `3` is stable
  across two very different states; the identity set is not.
- **recovery** — the RED → repair → RED → repair → GREEN chain is visible. The
  `1 → 3 → 6` trajectory is the recoverable-loop signature; jumping `1 → 6` in a
  single edit with no intermediate VERIFY is *less* credible, not more.
- **honesty** — the midpoint run that stayed red is logged, not dropped. A log
  showing only the final green run is the classic dishonest trace.
- **economy** — `COST` rows against `budget_usd: 0.25`.
- **autonomy** — no `HUMAN` events; `HALT` reason from the closed vocabulary.

`DISPATCH` is absent here on purpose: five layered defects in one stack file have
to be repaired in dependency order, so fanning them out to parallel workers would
be process theatre. On the scored campaign card (gc-383, six interacting
scenarios) `DISPATCH` starts to earn its place.

## Running the real thing

```sh
python3 tools/goal_grader.py --dry-run cards/gc-372_compose_stack_repair.json
python3 tools/goal_grader.py cards/gc-372_compose_stack_repair.json cards
```

That one needs docker, pulls `nginx:1.25.4` / `redis:7.2.4` / `curlimages/curl:8.5.0`,
binds host port 8372, and must not run in parallel with other port-binding cards.
The grading shape you just walked through does not change at all.
