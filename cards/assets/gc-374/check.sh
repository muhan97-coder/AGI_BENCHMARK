#!/usr/bin/env bash
# gc-374 SEALED HTTP contract check. Do not modify this file.
# Prints exactly one JSON line: {"checks_passed": N, "checks_total": 8}
set -u
cd "$(dirname "$0")"
NET=gc374net
WEB=gc374web
cleanup() { docker rm -f $WEB >/dev/null 2>&1; docker network rm $NET >/dev/null 2>&1; }
trap cleanup EXIT
cleanup
docker network create $NET >/dev/null 2>&1
docker run -d --name $WEB --network $NET \
  -v "$PWD/conf/nginx.conf":/etc/nginx/nginx.conf:ro \
  -v "$PWD/html":/usr/share/site:ro \
  nginx:1.25.4 >/dev/null 2>&1
sleep 4
CURL="docker run --rm --network $NET curlimages/curl:8.5.0 -s --max-time 10"
pass=0
total=8
# C1: GET / -> 200
code=$($CURL -o /dev/null -w '%{http_code}' "http://$WEB/" 2>/dev/null)
[ "$code" = "200" ] && pass=$((pass+1))
# C2: / body carries the landing token
$CURL "http://$WEB/" 2>/dev/null | grep -q "gc-374-home-ok" && pass=$((pass+1))
# C3: GET /health -> 200 with exact body "ok"
hcode=$($CURL -o /dev/null -w '%{http_code}' "http://$WEB/health" 2>/dev/null)
hbody=$($CURL "http://$WEB/health" 2>/dev/null)
[ "$hcode" = "200" ] && [ "$hbody" = "ok" ] && pass=$((pass+1))
# C4: GET /old -> 301 redirecting to /new
rcode=$($CURL -o /dev/null -w '%{http_code}' "http://$WEB/old" 2>/dev/null)
rloc=$($CURL -o /dev/null -w '%{redirect_url}' "http://$WEB/old" 2>/dev/null)
[ "$rcode" = "301" ] && printf '%s' "$rloc" | grep -q "/new" && pass=$((pass+1))
# C5: GET /new/ -> 200 with the moved token
ncode=$($CURL -o /dev/null -w '%{http_code}' "http://$WEB/new/" 2>/dev/null)
nbody=$($CURL "http://$WEB/new/" 2>/dev/null)
[ "$ncode" = "200" ] && printf '%s' "$nbody" | grep -q "gc-374-new-ok" && pass=$((pass+1))
# C6: unknown path -> 404
mcode=$($CURL -o /dev/null -w '%{http_code}' "http://$WEB/does-not-exist" 2>/dev/null)
[ "$mcode" = "404" ] && pass=$((pass+1))
# C7: X-Frame-Options: DENY on /
$CURL -D - -o /dev/null "http://$WEB/" 2>/dev/null | grep -i '^x-frame-options:' | grep -qi 'DENY' && pass=$((pass+1))
# C8: gzip negotiated on /
$CURL -H 'Accept-Encoding: gzip' -D - -o /dev/null "http://$WEB/" 2>/dev/null | grep -qi '^content-encoding:[[:space:]]*gzip' && pass=$((pass+1))
echo "{\"checks_passed\": $pass, \"checks_total\": $total}"
