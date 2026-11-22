#!/bin/bash
# A5 (2026-11-20): a scenario headless against assets_dev with --world xeen. Usage: walk_world.sh <scenario> <log name>
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
cd "$OYR"/output/studio_cal/x2/run
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 $OYR/build-xeen/game/openyamm --asset-root $OYR/assets_dev --world xeen \
  --headless-run-scenario "$1" --scenario-no-color > "$2" 2>&1
echo "exit $?" >> "$2"
