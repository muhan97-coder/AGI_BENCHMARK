#!/usr/bin/env bash
# gc-376 SEALED grader. Do not modify this file.
# Runs redis-benchmark (SET, 20000 ops, 32 clients) against redis:7.2.4 started with the
# sealed baseline config and then with tuned/redis.conf, back to back on the same machine.
# Durability is verified live via CONFIG GET on the tuned instance before benchmarking.
# Prints one JSON line with set_rps_ratio = tuned_set_rps / baseline_set_rps.
set -u
cd "$(dirname "$0")"
IMG=redis:7.2.4
NET=gc376net
cleanup() { docker rm -f gc376rb gc376rt >/dev/null 2>&1; docker network rm $NET >/dev/null 2>&1; }
trap cleanup EXIT
cleanup
docker network create $NET >/dev/null 2>&1
start_redis() {
  conf="$1"; name="$2"
  docker run -d --name "$name" --network $NET \
    -v "$PWD/$conf":/usr/local/etc/redis/redis.conf:ro \
    "$IMG" redis-server /usr/local/etc/redis/redis.conf >/dev/null 2>&1 || return 1
  for _ in $(seq 1 30); do
    [ "$(docker run --rm --network $NET $IMG redis-cli -h "$name" ping 2>/dev/null)" = "PONG" ] && return 0
    sleep 1
  done
  return 1
}
bench_set_rps() {
  name="$1"
  docker run --rm --network $NET "$IMG" redis-benchmark -h "$name" -t set -n 20000 -c 32 -q 2>/dev/null \
    | grep '^SET:' | grep -Eo '[0-9.]+' | head -1
}
start_redis baseline/redis.baseline.conf gc376rb || { echo '{"set_rps_ratio": 0, "reason": "baseline_start_failed"}'; exit 0; }
start_redis tuned/redis.conf gc376rt || { echo '{"set_rps_ratio": 0, "reason": "tuned_start_failed"}'; exit 0; }
aon=$(docker run --rm --network $NET $IMG redis-cli -h gc376rt config get appendonly 2>/dev/null | tail -1)
afs=$(docker run --rm --network $NET $IMG redis-cli -h gc376rt config get appendfsync 2>/dev/null | tail -1)
if [ "$aon" != "yes" ] || { [ "$afs" != "always" ] && [ "$afs" != "everysec" ]; }; then
  echo '{"set_rps_ratio": 0, "reason": "durability_guard_tripped"}'
  exit 0
fi
b=$(bench_set_rps gc376rb)
t=$(bench_set_rps gc376rt)
[ -z "$b" ] && b=0
[ -z "$t" ] && t=0
ratio=$(awk -v t="$t" -v b="$b" 'BEGIN { if (b <= 0 || t <= 0) print 0; else printf "%.3f", t / b }')
echo "{\"set_rps_ratio\": $ratio, \"baseline_set_rps\": $b, \"tuned_set_rps\": $t}"
