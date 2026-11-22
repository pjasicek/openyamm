#!/bin/bash
# A6: a scenario headless against assets_dev with --world xeen (and the rows mount until A2 writes X5's rows).
# Usage: walk.sh <scenario> <log name>
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
cd "$OYR"/output/studio_cal/x5/run
EXTRA=""
grep -q '^9103' $OYR/assets_dev/worlds/xeen/data_tables/map_stats.txt || \
  EXTRA="--extra-mount $OYR/output/studio_cal/x5/rows"
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $OYR/build-xeen/game/openyamm \
  --asset-root $OYR/assets_dev $EXTRA --world xeen \
  --headless-run-scenario "$1" --scenario-no-color > "$2" 2>&1
echo "exit $?" >> "$2"
