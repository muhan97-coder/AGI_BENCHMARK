#!/usr/bin/env bash
# gc-379 SEALED grader. Do not modify this file.
# Seeds a deterministic dataset, times the sealed query workload before and after
# applying tuned/optimize.sql (warm runs on both sides), and verifies the data was
# not modified via row counts + content hashes. Prints one JSON line with
# query_ms_ratio = optimized_ms / baseline_ms (99 = fail-closed sentinel).
set -u
cd "$(dirname "$0")"
IMG=postgres:12.22
NAME=gc379pg
cleanup() { docker rm -f $NAME >/dev/null 2>&1; }
trap cleanup EXIT
cleanup
docker run -d --name $NAME -e POSTGRES_PASSWORD=bench -e POSTGRES_USER=bench -e POSTGRES_DB=bench \
  -v "$PWD":/gc379:ro \
  -v "$PWD/tuned/postgresql.conf":/etc/postgresql/postgresql.conf:ro \
  "$IMG" -c config_file=/etc/postgresql/postgresql.conf >/dev/null 2>&1
ready=""
for _ in $(seq 1 60); do
  if docker exec $NAME pg_isready -U bench >/dev/null 2>&1; then ready=1; break; fi
  sleep 1
done
fail() { echo "{\"query_ms_ratio\": 99, \"reason\": \"$1\"}"; exit 0; }
[ -z "$ready" ] && fail "server_not_ready"
PSQL="docker exec $NAME psql -U bench -d bench -v ON_ERROR_STOP=1"
$PSQL -q -f /gc379/sql/seed.sql >/dev/null 2>&1 || fail "seed_failed"
integrity() {
  docker exec $NAME psql -U bench -d bench -Atc \
    "SELECT (SELECT count(*) || ':' || coalesce(sum(hashtext(o::text)::bigint), 0) FROM orders o) || '|' || (SELECT count(*) || ':' || coalesce(sum(hashtext(c::text)::bigint), 0) FROM customers c)" 2>/dev/null
}
run_ms() {
  $PSQL -f /gc379/sql/queries.sql 2>/dev/null | grep -Eo 'Time: [0-9.]+ ms' | awk '{ s += $2 } END { if (NR == 0) print 0; else printf "%.1f", s }'
}
sig1=$(integrity)
[ -z "$sig1" ] && fail "integrity_snapshot_failed"
run_ms >/dev/null            # warm-up pass, discarded
base_ms=$(run_ms)            # baseline = warm, pre-optimization
$PSQL -q -f /gc379/tuned/optimize.sql >/dev/null 2>&1 || fail "optimize_sql_errored"
docker exec $NAME psql -U bench -d bench -Atc "VACUUM ANALYZE" >/dev/null 2>&1
sig2=$(integrity)
[ "$sig1" != "$sig2" ] && fail "data_modified_by_optimize_sql"
run_ms >/dev/null            # warm-up pass under new physical design, discarded
opt_ms=$(run_ms)
ratio=$(awk -v t="$opt_ms" -v b="$base_ms" 'BEGIN { if (b <= 0 || t <= 0) print 99; else printf "%.3f", t / b }')
echo "{\"query_ms_ratio\": $ratio, \"baseline_ms\": $base_ms, \"optimized_ms\": $opt_ms}"
