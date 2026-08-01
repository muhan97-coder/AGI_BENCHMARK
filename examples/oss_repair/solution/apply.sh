#!/bin/sh
# Copy the reference solution into a workspace:  sh apply.sh <workspace>
# (Stages the pinned snapshot first if the agent has not done that step yet.)
set -e
[ -d "$1/work/ex-oss_repair/repo" ] || { mkdir -p "$1/work/ex-oss_repair"; cp -r "$1/assets/ex-oss_repair/upstream" "$1/work/ex-oss_repair/repo"; }
cp "$(dirname "$0")/repo/slugmini/__init__.py" "$1/work/ex-oss_repair/repo/slugmini/__init__.py"
