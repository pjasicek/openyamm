#!/bin/bash
# A5 (2026-11-20): a X6 scenario headless with --world xeen in one of lane A5's game slots.
#   walk.sh <scenario> <log> [asset root]     (default: assets_dev; the scratch root is output/studio_cal/x6/root)
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=${3:-$OYR/assets_dev}
cd "$OYR"/output/studio_cal/x6/run
SDL_AUDIODRIVER=dummy $OYR/level_generation/projects/xeen/common/run/game_slot.sh \
  "$OYR/tools/heavy.sh" 6 $OYR/build-xeen/game/openyamm --asset-root "$R" --world xeen \
  --headless-run-scenario "$1" --scenario-no-color > "$2" 2>&1
echo "exit $?" >> "$2"
