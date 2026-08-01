#!/usr/bin/env bash
# ex-infra_ops SEALED healthcheck. Do not modify this file.
# Prints exactly one JSON line: {"checks_passed": N, "checks_total": 6}
#
# Same six layers as the scored infra_ops cards (cf. cards/assets/gc-372/check.sh):
# parse -> pin -> start -> publish -> HTTP contract -> liveness. Only the runtime
# underneath is miniature (python3 minictl.py instead of docker compose).
set -u
cd "$(dirname "$0")"
P=exinfra
C="python3 minictl.py --project $P --stack stack/stack.json"
cleanup() { $C down >/dev/null 2>&1; }
trap cleanup EXIT
cleanup
pass=0
total=6
# C1: stack file parses
if $C config -q >/dev/null 2>&1; then pass=$((pass+1)); fi
# C2: every image pinned, no floating :latest tag
if $C config 2>/dev/null | grep -q "image:" && ! $C config 2>/dev/null | grep -q ":latest"; then
  pass=$((pass+1))
fi
$C up >/dev/null 2>&1
# C3: both services in running state
running=$($C ps --status running --services 2>/dev/null | wc -l)
if [ "$running" -eq 2 ]; then pass=$((pass+1)); fi
# C4: web published on host port 8391
addr=$($C port web 80 2>/dev/null)
if printf '%s' "$addr" | grep -q ":8391$"; then pass=$((pass+1)); fi
# C5: HTTP 200 with the content token, fetched by an independent stdlib client
body=$(python3 -c 'import sys,urllib.request
print(urllib.request.urlopen("http://" + sys.argv[1] + "/", timeout=5).read().decode())' \
  "${addr:-127.0.0.1:1}" 2>/dev/null)
if printf '%s' "$body" | grep -q "ex-infra-ops-stack-ok"; then pass=$((pass+1)); fi
# C6: cache answers PING
if [ "$($C exec cache cache-cli ping 2>/dev/null)" = "PONG" ]; then pass=$((pass+1)); fi
echo "{\"checks_passed\": $pass, \"checks_total\": $total}"
