#!/usr/bin/env bash
# gc-372 SEALED healthcheck. Do not modify this file.
# Prints exactly one JSON line: {"checks_passed": N, "checks_total": 6}
set -u
cd "$(dirname "$0")"
P=gc372bench
C="docker compose -p $P -f stack/docker-compose.yml"
cleanup() { $C down -v --remove-orphans >/dev/null 2>&1; }
trap cleanup EXIT
cleanup
pass=0
total=6
# C1: compose file parses
if $C config -q >/dev/null 2>&1; then pass=$((pass+1)); fi
# C2: every image pinned, no floating :latest tag
if $C config 2>/dev/null | grep -q "image:" && ! $C config 2>/dev/null | grep -q ":latest"; then
  pass=$((pass+1))
fi
$C up -d --quiet-pull >/dev/null 2>&1
sleep 8
# C3: both services in running state
running=$($C ps --status running --services 2>/dev/null | wc -l)
if [ "$running" -eq 2 ]; then pass=$((pass+1)); fi
# C4: web published on host port 8372
if $C port web 80 2>/dev/null | grep -q ":8372$"; then pass=$((pass+1)); fi
# C5: HTTP 200 with content token, checked via pinned curl on the stack network
net="${P}_default"
body=$(docker run --rm --network "$net" curlimages/curl:8.5.0 -fsS --max-time 10 http://web/ 2>/dev/null)
if printf '%s' "$body" | grep -q "gc-372-stack-ok"; then pass=$((pass+1)); fi
# C6: redis answers PING
if [ "$($C exec -T redis redis-cli ping 2>/dev/null)" = "PONG" ]; then pass=$((pass+1)); fi
echo "{\"checks_passed\": $pass, \"checks_total\": $total}"
