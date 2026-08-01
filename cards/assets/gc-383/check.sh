#!/usr/bin/env bash
# gc-383 SEALED campaign harness. Do not modify this file.
# Runs six ops scenarios against the stack in stack/docker-compose.yml and prints
# exactly one JSON line: {"scenarios_passed": N, "scenarios_total": 6}
set -u
cd "$(dirname "$0")"
P=gc383bench
C="docker compose -p $P -f stack/docker-compose.yml"
NETNAME="${P}_default"
CURLIMG=curlimages/curl:8.5.0
cleanup() { $C down -v --remove-orphans >/dev/null 2>&1; }
trap cleanup EXIT
cleanup
pass=0
total=6
wait_all_healthy() {
  tries="$1"
  for _ in $(seq 1 "$tries"); do
    n=0
    for s in web cache db worker; do
      cid=$($C ps -q "$s" 2>/dev/null)
      [ -z "$cid" ] && continue
      st=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$cid" 2>/dev/null)
      [ "$st" = "healthy" ] && n=$((n+1))
    done
    [ "$n" -eq 4 ] && return 0
    sleep 3
  done
  return 1
}
# S1: config parses, every image pinned (no :latest)
s1=0
if $C config -q >/dev/null 2>&1; then
  if $C config 2>/dev/null | grep -q "image:" && ! $C config 2>/dev/null | grep -q ":latest"; then s1=1; fi
fi
[ "$s1" = "1" ] && pass=$((pass+1))
$C up -d --quiet-pull >/dev/null 2>&1
# S2: all four services define healthchecks and all reach healthy within ~90s
hc=$($C config 2>/dev/null | grep -c 'healthcheck:')
if [ "$hc" -ge 4 ] && wait_all_healthy 30; then pass=$((pass+1)); fi
# S3: HTTP contract -- token on / and 200 on /health
body=$(docker run --rm --network "$NETNAME" $CURLIMG -fsS --max-time 10 http://web/ 2>/dev/null)
hcode=$(docker run --rm --network "$NETNAME" $CURLIMG -s -o /dev/null --max-time 10 -w '%{http_code}' http://web/health 2>/dev/null)
if printf '%s' "$body" | grep -q "gc-383-web-ok" && [ "$hcode" = "200" ]; then pass=$((pass+1)); fi
# S4: cache persistence across service restart
$C exec -T cache redis-cli set gc383key sealed-v1 >/dev/null 2>&1
sleep 2
$C restart cache >/dev/null 2>&1
sleep 4
v=$($C exec -T cache redis-cli get gc383key 2>/dev/null)
[ "$v" = "sealed-v1" ] && pass=$((pass+1))
# S5: db + cache state survives full down/up (named volumes required)
$C exec -T db psql -U app -d appdb -Atc "CREATE TABLE IF NOT EXISTS probe (id int); INSERT INTO probe VALUES (1)" >/dev/null 2>&1
$C exec -T cache redis-cli set gc383key2 sealed-v2 >/dev/null 2>&1
sleep 2
$C down >/dev/null 2>&1
$C up -d >/dev/null 2>&1
wait_all_healthy 30 >/dev/null 2>&1
rows=$($C exec -T db psql -U app -d appdb -Atc "SELECT count(*) FROM probe" 2>/dev/null)
v2=$($C exec -T cache redis-cli get gc383key2 2>/dev/null)
if [ "${rows:-0}" -ge 1 ] 2>/dev/null && [ "$v2" = "sealed-v2" ]; then pass=$((pass+1)); fi
# S6: worker self-heals after a kill (restart policy)
wid=$($C ps -q worker 2>/dev/null)
if [ -n "$wid" ]; then
  docker kill "$wid" >/dev/null 2>&1
  sleep 20
  if $C ps --status running --services 2>/dev/null | grep -qx worker; then pass=$((pass+1)); fi
fi
echo "{\"scenarios_passed\": $pass, \"scenarios_total\": $total}"
