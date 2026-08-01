#!/usr/bin/env bash
# gc-377 SEALED grader. Do not modify this file.
# Warms 10 distinct URLs through the proxy, then issues 40 more requests over the same
# URLs and computes cache_hit_rate from the origin's own request counter.
# Prints one JSON line with cache_hit_rate.
set -u
cd "$(dirname "$0")"
NET=gc377net
APP=gc377app
WEB=gc377web
CURLIMG=curlimages/curl:8.5.0
cleanup() { docker rm -f $APP $WEB >/dev/null 2>&1; docker network rm $NET >/dev/null 2>&1; }
trap cleanup EXIT
cleanup
docker network create $NET >/dev/null 2>&1
docker run -d --name $APP --network $NET -v "$PWD/upstream":/app:ro python:3.11.9-slim python /app/app.py >/dev/null 2>&1
docker run -d --name $WEB --network $NET -v "$PWD/conf/nginx.conf":/etc/nginx/nginx.conf:ro nginx:1.25.4 >/dev/null 2>&1
sleep 4
count_upstream() {
  docker run --rm --network $NET $CURLIMG -s --max-time 10 "http://$APP:9000/__count" 2>/dev/null | grep -Eo '[0-9]+' | head -1
}
n0=$(count_upstream); [ -z "$n0" ] && n0=-1
warm_args=""
for u in 0 1 2 3 4 5 6 7 8 9; do warm_args="$warm_args -o /dev/null http://$WEB/api/item/$u"; done
warm_codes=$(docker run --rm --network $NET $CURLIMG -s --max-time 60 -w '%{http_code}\n' $warm_args 2>/dev/null)
meas_args=""
for _ in 1 2 3 4; do
  for u in 0 1 2 3 4 5 6 7 8 9; do meas_args="$meas_args -o /dev/null http://$WEB/api/item/$u"; done
done
meas_codes=$(docker run --rm --network $NET $CURLIMG -s --max-time 120 -w '%{http_code}\n' $meas_args 2>/dev/null)
n2=$(count_upstream); [ -z "$n2" ] && n2=-1
bad=$(printf '%s\n%s\n' "$warm_codes" "$meas_codes" | grep -cv '^200$')
nreq=$(printf '%s\n%s\n' "$warm_codes" "$meas_codes" | grep -c '^200$')
if [ "$n0" -lt 0 ] || [ "$n2" -lt 0 ] || [ "$bad" -gt 0 ] || [ "$nreq" -ne 50 ]; then
  echo "{\"cache_hit_rate\": 0, \"reason\": \"non_200_or_counter_unreachable\", \"non_200\": $bad}"
  exit 0
fi
misses=$((n2 - n0))
rate=$(awk -v m="$misses" 'BEGIN { h = (50 - m) / 40.0; if (h < 0) h = 0; if (h > 1) h = 1; printf "%.3f", h }')
echo "{\"cache_hit_rate\": $rate, \"origin_misses\": $misses, \"requests\": 50}"
