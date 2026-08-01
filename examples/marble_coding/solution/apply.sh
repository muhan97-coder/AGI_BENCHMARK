#!/bin/sh
# usage: sh apply.sh <workspace>   — copies the reference solution into the workspace
set -eu
mkdir -p "${1:?usage: sh apply.sh <workspace>}/workspace" && cp -R "$(dirname "$0")/workspace/." "$1/workspace/"
