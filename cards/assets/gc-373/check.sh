#!/usr/bin/env bash
# gc-373 SEALED grader. Do not modify this file.
# Runs pgbench (fixed seed, scale 10) once under the sealed baseline config and once
# under tuned/postgresql.conf on the same machine, then prints one JSON line with tps_ratio.
set -u
cd "$(dirname "$0")"
IMG=postgres:12.22
cleanup() { docker rm -f gc373pgb gc373pgt >/dev/null 2>&1; }
trap cleanup EXIT
cleanup
if grep -Eiq '^[[:space:]]*fsync[[:space:]]*=[[:space:]]*off|^[[:space:]]*full_page_writes[[:space:]]*=[[:space:]]*off' tuned/postgresql.conf; then
  echo '{"tps_ratio": 0, "reason": "durability_guard_tripped"}'
  exit 0
fi
run_tps() {
  conf="$1"; name="$2"
  docker rm -f "$name" >/dev/null 2>&1
  docker run -d --name "$name" -e POSTGRES_PASSWORD=bench -e POSTGRES_USER=bench -e POSTGRES_DB=bench \
    -v "$PWD/$conf":/etc/postgresql/postgresql.conf:ro "$IMG" \
    -c config_file=/etc/postgresql/postgresql.conf >/dev/null 2>&1 || { echo 0; return; }
  ready=""
  for _ in $(seq 1 60); do
    if docker exec "$name" pg_isready -U bench >/dev/null 2>&1; then ready=1; break; fi
    sleep 1
  done
  [ -z "$ready" ] && { echo 0; return; }
  docker exec "$name" pgbench -i -s 10 -U bench bench >/dev/null 2>&1 || { echo 0; return; }
  docker exec "$name" pgbench --random-seed=42 -c 8 -j 2 -T 20 -U bench bench 2>/dev/null \
    | grep -m1 -Eo 'tps = [0-9.]+' | grep -Eo '[0-9.]+' | head -1
}
b=$(run_tps baseline/postgresql.baseline.conf gc373pgb | tail -1)
t=$(run_tps tuned/postgresql.conf gc373pgt | tail -1)
[ -z "$b" ] && b=0
[ -z "$t" ] && t=0
ratio=$(awk -v t="$t" -v b="$b" 'BEGIN { if (b <= 0 || t <= 0) print 0; else printf "%.3f", t / b }')
echo "{\"tps_ratio\": $ratio, \"baseline_tps\": $b, \"tuned_tps\": $t}"
