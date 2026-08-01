#!/usr/bin/env bash
# gc-381 SEALED SLO grader. Do not modify this file.
# Phase A: warm 10 URLs, then 200 requests over the same URLs; measures error count,
# p95 latency, and origin hits (from the origin's own counter).
# Phase B: waits past the 30s TTL, stops the origin, and requires the edge to keep
# serving 200s from stale cache. Prints one JSON line with slo_checks_passed (0..5).
set -u
cd "$(dirname "$0")"
NET=gc381net
APP=gc381app
WEB=gc381web
CURLIMG=curlimages/curl:8.5.0
cleanup() { docker rm -f $APP $WEB >/dev/null 2>&1; docker network rm $NET >/dev/null 2>&1; }
trap cleanup EXIT
cleanup
docker network create $NET >/dev/null 2>&1
docker run -d --name $APP --network $NET -v "$PWD/upstream":/app:ro python:3.11.9-slim python /app/app.py >/dev/null 2>&1
docker run -d --name $WEB --network $NET -v "$PWD/conf/nginx.conf":/etc/nginx/nginx.conf:ro nginx:1.25.4 >/dev/null 2>&1
sleep 4
count_origin() {
  docker run --rm --network $NET $CURLIMG -s --max-time 10 "http://$APP:9000/__count" 2>/dev/null | grep -Eo '[0-9]+' | head -1
}
n0=$(count_origin); [ -z "$n0" ] && n0=-1
warm_args=""
for u in 0 1 2 3 4 5 6 7 8 9; do warm_args="$warm_args -o /dev/null http://$WEB/api/item/$u"; done
docker run --rm --network $NET $CURLIMG -s --max-time 60 $warm_args >/dev/null 2>&1
n1=$(count_origin); [ -z "$n1" ] && n1=-1
meas_args=""
for _ in $(seq 1 20); do
  for u in 0 1 2 3 4 5 6 7 8 9; do meas_args="$meas_args -o /dev/null http://$WEB/api/item/$u"; done
done
meas=$(docker run --rm --network $NET $CURLIMG -s --max-time 240 -w '%{http_code} %{time_total}\n' $meas_args 2>/dev/null)
n2=$(count_origin); [ -z "$n2" ] && n2=-1
nlines=$(printf '%s\n' "$meas" | grep -c '.')
non200=$(printf '%s\n' "$meas" | awk '$1 != "200" { c++ } END { print c + 0 }')
p95=$(printf '%s\n' "$meas" | awk '{ print $2 }' | sort -n | awk '{ a[NR] = $1 } END { if (NR == 0) print 999; else { i = int(NR * 0.95); if (i < 1) i = 1; print a[i] } }')
pass=0
# C1: all 200 measured requests returned HTTP 200
[ "$nlines" -eq 200 ] && [ "$non200" -eq 0 ] && pass=$((pass+1))
# C2: p95 latency <= 150ms (origin alone costs 200ms, so this requires cache hits)
awk -v p="$p95" 'BEGIN { exit !(p <= 0.15) }' && pass=$((pass+1))
# C3: at most 15 requests reached the origin during the measurement window
if [ "$n1" -ge 0 ] && [ "$n2" -ge 0 ]; then
  delta=$((n2 - n1))
  [ "$delta" -le 15 ] && pass=$((pass+1))
else
  delta=-1
fi
# C4: cache hit rate >= 0.90 over the measurement window
if [ "$delta" -ge 0 ]; then
  awk -v d="$delta" 'BEGIN { exit !((200 - d) / 200.0 >= 0.90) }' && pass=$((pass+1))
fi
# C5: stale-serving -- past TTL and with the origin dead, the edge still answers 200
sleep 31
docker stop $APP >/dev/null 2>&1
scode=$(docker run --rm --network $NET $CURLIMG -s -o /dev/null --max-time 15 -w '%{http_code}' "http://$WEB/api/item/3" 2>/dev/null)
[ "$scode" = "200" ] && pass=$((pass+1))
echo "{\"slo_checks_passed\": $pass, \"slo_checks_total\": 5, \"non_200\": $non200, \"p95_s\": $p95, \"origin_delta\": $delta, \"stale_code\": \"${scode:-none}\"}"
