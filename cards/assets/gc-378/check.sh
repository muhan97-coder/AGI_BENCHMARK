#!/usr/bin/env bash
# gc-378 SEALED healthcheck. Do not modify this file.
# Prints exactly one JSON line: {"checks_passed": N, "checks_total": 10}
set -u
cd "$(dirname "$0")"
P=gc378bench
C="docker compose -p $P -f stack/docker-compose.yml"
cleanup() { $C down -v --remove-orphans >/dev/null 2>&1; }
trap cleanup EXIT
cleanup
pass=0
total=10
# C1: compose file parses
if $C config -q >/dev/null 2>&1; then pass=$((pass+1)); fi
# C2: no floating :latest tags anywhere
if $C config 2>/dev/null | grep -q "image:" && ! $C config 2>/dev/null | grep -q ":latest"; then
  pass=$((pass+1))
fi
$C up -d --quiet-pull >/dev/null 2>&1
sleep 20
# C3: all four services running
running=$($C ps --status running --services 2>/dev/null | wc -l)
if [ "$running" -eq 4 ]; then pass=$((pass+1)); fi
# C4: web published on host port 8378
if $C port web 80 2>/dev/null | grep -q ":8378$"; then pass=$((pass+1)); fi
# C5: web serves the content token
net="${P}_default"
body=$(docker run --rm --network "$net" curlimages/curl:8.5.0 -fsS --max-time 10 http://web/ 2>/dev/null)
if printf '%s' "$body" | grep -q "gc-378-web-ok"; then pass=$((pass+1)); fi
# C6: cache is NOT published to the host
if [ -z "$($C port cache 6379 2>/dev/null)" ]; then pass=$((pass+1)); fi
# C7: db accepts connections as app/appdb
if $C exec -T db pg_isready -U app -d appdb >/dev/null 2>&1; then pass=$((pass+1)); fi
# C8: sealed schema seed was applied (3 rows in items)
rows=$($C exec -T db psql -U app -d appdb -Atc "SELECT count(*) FROM items" 2>/dev/null)
if [ "${rows:-0}" -ge 3 ] 2>/dev/null; then pass=$((pass+1)); fi
# C9: worker heartbeat lands in redis
hb=$($C exec -T cache redis-cli get heartbeat 2>/dev/null)
if [ -n "$hb" ] && [ "$hb" != "(nil)" ]; then pass=$((pass+1)); fi
# C10: worker carries a restart policy (unless-stopped or always)
wid=$($C ps -q worker 2>/dev/null)
rp=""
[ -n "$wid" ] && rp=$(docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' "$wid" 2>/dev/null)
if [ "$rp" = "unless-stopped" ] || [ "$rp" = "always" ]; then pass=$((pass+1)); fi
echo "{\"checks_passed\": $pass, \"checks_total\": $total}"
