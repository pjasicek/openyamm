#!/bin/bash
# Rebase (A5): X1's walk or another scenario headless against output/studio_cal/x1/xroot. Usage: walk_rb.sh <scenario> <log name>
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
cd "$OYR"/output/studio_cal/x1/run
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 $OYR/build-xeen/game/openyamm --asset-root $OYR/output/studio_cal/x1/xroot --world mm7 \
  --headless-run-scenario "$1" --scenario-no-color > "$2" 2>&1
echo "exit $?" >> "$2"
