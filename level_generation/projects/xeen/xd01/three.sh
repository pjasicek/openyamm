#!/bin/bash
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR
X=$R/output/studio_cal/xd01
cd $X/run
for n in 1 2 3; do
  "$OYR/tools/heavy.sh" 6 timeout 1200 $R/build/game/openyamm --asset-root $R/assets_dev --extra-mount $X/mount --world mm7 --headless-run-scenario $R/devdocs/xeen/briefs/xd01/L4/playtest.yml --scenario-no-color > final$n.log 2>&1
  echo "run $n exit $? passed $(grep -c '^PASS' final$n.log)"
done > three.out
