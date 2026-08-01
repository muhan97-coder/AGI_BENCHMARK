#!/bin/sh
# usage: sh apply.sh <workspace>   — copies the reference solution into the workspace
set -eu
mkdir -p "${1:?usage: sh apply.sh <workspace>}/work" && cp -R "$(dirname "$0")/work/." "$1/work/"
