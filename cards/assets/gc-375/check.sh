#!/usr/bin/env bash
# gc-375 SEALED grader. Do not modify this file.
# Measures pgbench per-transaction p95 latency (scale 10, seed 42, 8 clients, 25s)
# under the sealed baseline config and under tuned/postgresql.conf, back to back on
# the same machine. Prints one JSON line with p95_ratio = tuned_p95 / baseline_p95.
set -u
cd "$(dirname "$0")"
IMG=postgres:12.22
cleanup() { docker rm -f gc375pgb gc375pgt >/dev/null 2>&1; }
trap cleanup EXIT
cleanup
if grep -Eiq '^[[:space:]]*fsync[[:space:]]*=[[:space:]]*off|^[[:space:]]*full_page_writes[[:space:]]*=[[:space:]]*off' tuned/postgresql.conf; then
  echo '{"p95_ratio": 99, "reason": "durability_guard_tripped"}'
  exit 0
fi
run_p95_ms() {
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
  docker exec "$name" bash -c "cd /tmp && rm -f gc375log.* && pgbench --random-seed=42 -c 8 -j 2 -T 25 -l --log-prefix=gc375log -U bench bench >/dev/null 2>&1; cat gc375log.* 2>/dev/null | sort -n -k3 | awk '{a[NR]=\$3} END { if (NR == 0) print 0; else { i = int(NR * 0.95); if (i < 1) i = 1; printf \"%.3f\", a[i] / 1000.0 } }'"
}
b=$(run_p95_ms baseline/postgresql.baseline.conf gc375pgb | tail -1)
t=$(run_p95_ms tuned/postgresql.conf gc375pgt | tail -1)
[ -z "$b" ] && b=0
[ -z "$t" ] && t=0
ratio=$(awk -v t="$t" -v b="$b" 'BEGIN { if (b <= 0 || t <= 0) print 99; else printf "%.3f", t / b }')
echo "{\"p95_ratio\": $ratio, \"baseline_p95_ms\": $b, \"tuned_p95_ms\": $t}"
