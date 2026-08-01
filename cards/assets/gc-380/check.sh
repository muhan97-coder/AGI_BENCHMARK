#!/usr/bin/env bash
# gc-380 SEALED grader. Do not modify this file.
# Connection ladder through pgbouncer: pgbench -S -C at 50, 100, 200 clients (15s each,
# fixed seed). A stage passes when pgbench exits 0 with tps > 0; stage 3 additionally
# requires tps@200 >= 0.5 * tps@50 (no throughput collapse under connection pressure).
# Prints one JSON line with stages_ok (0..3).
set -u
cd "$(dirname "$0")"
NET=gc380net
PG=gc380pg
BNC=gc380bnc
cleanup() { docker rm -f $PG $BNC >/dev/null 2>&1; docker network rm $NET >/dev/null 2>&1; }
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
[ -z "$ready" ] && { echo '{"stages_ok": 0, "reason": "postgres_not_ready"}'; exit 0; }
docker exec $PG pgbench -i -s 10 -U bench bench >/dev/null 2>&1 || { echo '{"stages_ok": 0, "reason": "init_failed"}'; exit 0; }
docker run -d --name $BNC --network $NET \
  -v "$PWD/tuned/pgbouncer.ini":/etc/pgbouncer/pgbouncer.ini:ro \
  -v "$PWD/sealed/userlist.txt":/etc/pgbouncer/userlist.txt:ro \
  --entrypoint pgbouncer edoburu/pgbouncer:v1.23.1-p2 /etc/pgbouncer/pgbouncer.ini >/dev/null 2>&1
sleep 4
stage_tps() {
  clients="$1"
  out=$(docker run --rm --network $NET -e PGPASSWORD=bench postgres:12.22 \
    pgbench -h $BNC -p 6432 -U bench -S -C -c "$clients" -j 4 -T 15 --random-seed=42 bench 2>/dev/null)
  rc=$?
  if [ $rc -ne 0 ]; then echo ""; return; fi
  printf '%s\n' "$out" | grep -m1 -Eo 'tps = [0-9.]+' | grep -Eo '[0-9.]+' | head -1
}
t50=$(stage_tps 50)
t100=$(stage_tps 100)
t200=$(stage_tps 200)
ok=0
positive() { awk -v x="${1:-0}" 'BEGIN { exit !(x > 0) }'; }
[ -n "$t50" ] && positive "$t50" && ok=$((ok+1))
[ -n "$t100" ] && positive "$t100" && ok=$((ok+1))
if [ -n "$t200" ] && positive "$t200" && [ -n "$t50" ] && positive "$t50"; then
  if awk -v a="$t200" -v b="$t50" 'BEGIN { exit !(a >= 0.5 * b) }'; then ok=$((ok+1)); fi
fi
echo "{\"stages_ok\": $ok, \"tps_50\": ${t50:-0}, \"tps_100\": ${t100:-0}, \"tps_200\": ${t200:-0}}"
