#!/bin/bash
# A6 D6: a scenario headless with --world xeen against an asset root (default the pre-test stage; D6_ASSETS=assets_dev
# after the install), with the rows mount while A2's map_stats row 9113 is missing. Usage: walk.sh <scenario> <log>
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
cd "$OYR"/output/studio_cal/d6/run
ROOT=${D6_ASSETS:-$OYR/output/studio_cal/d6/stage/assets_dev}
EXTRA=""
grep -q '^9113' $ROOT/worlds/xeen/data_tables/map_stats.txt || EXTRA="--extra-mount $OYR/output/studio_cal/d6/rows"
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $OYR/build-xeen/game/openyamm \
  --asset-root $ROOT $EXTRA --world xeen \
  --headless-run-scenario "$1" --scenario-no-color > "$2" 2>&1
echo "exit $?" >> "$2"
