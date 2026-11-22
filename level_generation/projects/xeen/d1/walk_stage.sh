#!/bin/bash
# A6 D1 (2026-11-20): walk.sh against a pre-test stage (output/studio_cal/d1/stage_pre/assets_dev) before the install.
# Usage: walk_stage.sh <scenario> <log name>
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
cd "$OYR"/output/studio_cal/d1/run
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $OYR/build-xeen/game/openyamm \
  --asset-root $OYR/output/studio_cal/d1/stage_pre/assets_dev --world xeen \
  --headless-run-scenario "$1" --scenario-no-color > "$2" 2>&1
echo "exit $?" >> "$2"
