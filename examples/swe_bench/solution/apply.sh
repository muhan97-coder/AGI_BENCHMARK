#!/bin/sh
# Copy the reference solution into a workspace:  sh apply.sh <workspace>
set -e
mkdir -p "$1/runs/ex-swe_bench" && cp "$(dirname "$0")/predictions.jsonl" "$1/runs/ex-swe_bench/predictions.jsonl"
