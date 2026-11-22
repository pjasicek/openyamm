#!/bin/bash
# The playtest four times on the installed mount (go.sh builds and installs first).
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR
X=$R/output/studio_cal/xd02
L=$R/devdocs/xeen/briefs/xd02/L4
mkdir -p $X/run; cd $X/run
for n in 1 2 3 4; do
  "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build/game/openyamm --asset-root $R/assets_dev --extra-mount $X/mount --world mm7 --headless-run-scenario $L/playtest.yml --scenario-no-color > final_$n.log 2>&1
  echo "run $n exit $? passed $(grep -c '^PASS' final_$n.log) of $(grep -o 'steps=[0-9]*' final_$n.log | head -1) $(grep -E '^Scenario failure' final_$n.log | head -1)"
done > four.out
