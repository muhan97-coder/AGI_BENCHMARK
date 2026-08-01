#!/bin/bash
# gc-382 SEALED client loop. Do not modify this file.
# Inserts rows one at a time for 15 seconds and records every server-acknowledged id.
# The acked file is the ground truth for the durability check after the crash.
: > /tmp/acked.txt
end=$((SECONDS + 15))
while [ $SECONDS -lt $end ]; do
  id=$(psql -h gc382pg -U bench -d bench -Atqc "INSERT INTO ledger(v) VALUES ('x') RETURNING id" 2>/dev/null)
  if [ -n "$id" ]; then
    echo "$id" >> /tmp/acked.txt
  fi
done
# Stay alive so the grader can read /tmp/acked.txt afterwards.
sleep 600
