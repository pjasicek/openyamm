#!/bin/bash
# A5 (2026-11-20, fifth session): a scenario headless against X3's scratch root (root.sh: X3's map_stats and travel
# rows until A2 writes them) with --world xeen. Usage: walk.sh <scenario> <log> [asset root]
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
cd "$OYR"/output/studio_cal/x3/run
R=${3:-$OYR/output/studio_cal/x3/root}
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 $OYR/build-xeen/game/openyamm --asset-root "$R" --world xeen \
  --headless-run-scenario "$1" --scenario-no-color > "$2" 2>&1
echo "exit $?" >> "$2"
