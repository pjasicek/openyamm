#!/bin/bash
# A6: a D2 scenario headless against assets_dev with --world xeen. Usage: walk.sh <scenario> <log name>
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
cd "$OYR"/output/studio_cal/d2/run
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $OYR/build-xeen/game/openyamm \
  --asset-root ${D2_ASSETS:-$OYR/assets_dev} --world xeen \
  --headless-run-scenario "$1" --scenario-no-color > "$2" 2>&1
echo "exit $?" >> "$2"
