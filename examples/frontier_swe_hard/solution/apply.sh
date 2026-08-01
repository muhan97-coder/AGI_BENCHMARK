#!/bin/sh
# Copy the reference solution into a workspace:  sh apply.sh <workspace> [predictions_file]
set -e
mkdir -p "$1/runs/ex-frontier_swe_hard" && cp "$(dirname "$0")/${2:-predictions.jsonl}" "$1/runs/ex-frontier_swe_hard/predictions.jsonl"
