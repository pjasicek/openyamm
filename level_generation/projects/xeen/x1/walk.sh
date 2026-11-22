#!/bin/bash
# Play X1's walk headless against the scratch root (which holds XD-01 to XD-05 from xeen_root). Log in run/walk_<n>.log
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
cd "$OYR"
C=output/studio_cal/x1
mkdir -p $C/run
N=${1:-1}
cd $C/run
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 $OYR/build/game/openyamm --asset-root $OYR/$C/root --world mm7 \
  --headless-run-scenario $OYR/devdocs/xeen/briefs/x1/L4/playtest.yml --scenario-no-color > walk_$N.log 2>&1
echo "exit $?" >> walk_$N.log
