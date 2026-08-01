#!/usr/bin/env bash
# gc-382 SEALED crash-durability grader. Do not modify this file.
# Starts postgres under tuned/postgresql.conf, runs a sealed acked-insert loop,
# SIGKILLs the server mid-load (simulated power loss), restarts it on the same data
# directory, and verifies: durable settings, recovery time, zero acked-commit loss,
# and a minimum insert floor. Prints one JSON line with checks_passed (0..4).
set -u
cd "$(dirname "$0")"
NET=gc382net
PG=gc382pg
CL=gc382cl
cleanup() { docker rm -f $PG $CL >/dev/null 2>&1; docker network rm $NET >/dev/null 2>&1; }
trap cleanup EXIT
cleanup
docker network create $NET >/dev/null 2>&1
docker run -d --name $PG --network $NET -e POSTGRES_PASSWORD=bench -e POSTGRES_USER=bench -e POSTGRES_DB=bench \
  -v "$PWD/tuned/postgresql.conf":/etc/postgresql/postgresql.conf:ro \
  postgres:12.22 -c config_file=/etc/postgresql/postgresql.conf >/dev/null 2>&1
ready=""
for _ in $(seq 1 60); do
  if docker exec $PG pg_isready -U bench >/dev/null 2>&1; then ready=1; break; fi
  sleep 1
done
[ -z "$ready" ] && { echo '{"checks_passed": 0, "checks_total": 4, "reason": "server_not_ready"}'; exit 0; }
docker exec $PG psql -U bench -d bench -Atc "CREATE TABLE ledger (id bigserial PRIMARY KEY, v text NOT NULL)" >/dev/null 2>&1
pass=0
# C1: durable settings live on the server
f=$(docker exec $PG psql -U bench -d bench -Atc "SHOW fsync" 2>/dev/null)
fp=$(docker exec $PG psql -U bench -d bench -Atc "SHOW full_page_writes" 2>/dev/null)
sc=$(docker exec $PG psql -U bench -d bench -Atc "SHOW synchronous_commit" 2>/dev/null)
if [ "$f" = "on" ] && [ "$fp" = "on" ] && [ "$sc" = "on" ]; then
  pass=$((pass+1))
else
  echo '{"checks_passed": 0, "checks_total": 4, "reason": "durability_settings_off"}'
  exit 0
fi
# Sealed load: single-row inserts, each acked id recorded client-side
docker run -d --name $CL --network $NET -e PGPASSWORD=bench \
  -v "$PWD/sealed/insert_loop.sh":/loop.sh:ro postgres:12.22 bash /loop.sh >/dev/null 2>&1
sleep 10
# Simulated power loss mid-load
docker kill -s KILL $PG >/dev/null 2>&1
sleep 7
# C2: crash recovery back to accepting connections within 60s
docker start $PG >/dev/null 2>&1
rec=""
t0=$SECONDS
for _ in $(seq 1 60); do
  if docker exec $PG pg_isready -U bench >/dev/null 2>&1; then rec=$((SECONDS - t0)); break; fi
  sleep 1
done
[ -n "$rec" ] && pass=$((pass+1))
n_acked=$(docker exec $CL bash -c 'wc -l < /tmp/acked.txt' 2>/dev/null | tr -d '[:space:]')
last=$(docker exec $CL bash -c 'tail -1 /tmp/acked.txt' 2>/dev/null | tr -d '[:space:]')
[ -z "$n_acked" ] && n_acked=0
[ -z "$last" ] && last=0
# C3: every acknowledged commit survived the crash
if [ -n "$rec" ] && [ "$n_acked" -gt 0 ] && [ "$last" -gt 0 ] 2>/dev/null; then
  have_last=$(docker exec $PG psql -U bench -d bench -Atc "SELECT count(*) FROM ledger WHERE id = $last" 2>/dev/null)
  upto=$(docker exec $PG psql -U bench -d bench -Atc "SELECT count(*) FROM ledger WHERE id <= $last" 2>/dev/null)
  if [ "${have_last:-0}" = "1" ] && [ "${upto:-0}" -ge "$n_acked" ] 2>/dev/null; then pass=$((pass+1)); fi
fi
# C4: sanity floor -- the load actually ran (>= 200 acked inserts in ~10s window)
[ "$n_acked" -ge 200 ] 2>/dev/null && pass=$((pass+1))
echo "{\"checks_passed\": $pass, \"checks_total\": 4, \"acked\": $n_acked, \"recovery_s\": ${rec:-999}}"
