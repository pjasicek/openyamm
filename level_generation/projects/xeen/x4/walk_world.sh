#!/bin/bash
# A5 X4 (2026-11-20): a scenario headless against an asset root with --world xeen, in one of lane A5's two game slots.
#   walk_world.sh <scenario> <log name> [asset root]      (default root: assets_dev)
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
root=${3:-$OYR/assets_dev}
cd "$OYR"/output/studio_cal/x4/run
SDL_AUDIODRIVER=dummy $OYR/level_generation/projects/xeen/common/run/game_slot.sh \
  "$OYR/tools/heavy.sh" 6 $OYR/build-xeen/game/openyamm --asset-root "$root" --world xeen \
  --headless-run-scenario "$1" --scenario-no-color > "$2" 2>&1
echo "exit $?" >> "$2"
