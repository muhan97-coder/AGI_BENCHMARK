#!/bin/sh
# usage: solution/apply.sh <workspace>   — drop the reference solution into a workspace
cp -a "$(dirname "$0")/files/." "${1:?usage: apply.sh <workspace>}/"
