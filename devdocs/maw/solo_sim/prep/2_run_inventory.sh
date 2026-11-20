#!/bin/bash
# Step 2. Runs the 24 inventory scenarios headless, 12 at a time (about 10 minutes); each log is <scenario>.log.
set -e
P="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$P/../../../.." && pwd)"
S="${SOLO_SIM_DIR:-$REPO/output/maw_solo_sim}"
cd "$REPO"
ls "$S"/inv/inv_*.yml | xargs -P 12 -I{} sh -c './build/game/openyamm --headless-run-scenario {} > {}.log 2>&1'
for f in "$S"/inv/inv_*.yml.log; do echo "$(basename "$f") maps $(grep -c 'slain' "$f") passed $(grep -c 'Scenario passed' "$f")"; done
