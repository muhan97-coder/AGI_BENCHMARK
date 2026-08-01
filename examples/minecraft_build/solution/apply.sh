#!/bin/sh
# usage: solution/apply.sh <workspace>   — drop the reference solution into a workspace
#
# The agent-authored deliverables are the build plan and the two ledgers; the
# score file is written by the sealed judger, never by hand. So this script
# stages the arena if the agent has not run 'judger.py prepare' yet, copies the
# deliverables in, and then replays the tape through the judger — leaving a
# workspace the card's success command can actually grade.
set -e
WS="${1:?usage: apply.sh <workspace>}"
[ -f "$WS/work/ex-minecraft_build/.cache/load_status.cache" ] || \
  (cd "$WS" && python3 assets/ex-minecraft_build/judger.py prepare \
      --task ex-minecraft_build --idx 0 --agent_names builder_a >/dev/null)
cp -a "$(dirname "$0")/files/." "$WS/"
cd "$WS" && exec python3 assets/ex-minecraft_build/judger.py run \
    --task ex-minecraft_build --idx 0 --agent_names builder_a
