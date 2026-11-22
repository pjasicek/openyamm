#!/bin/bash
# Third pass: the two playtests, four runs each, on mount3/.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR
X=$R/output/studio_cal/xd01
L=$R/devdocs/xeen/briefs/xd01/L4
cd $X/run3
for n in 1 2 3 4; do
  for t in playtest playtest_perception; do
    "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build/game/openyamm --asset-root $R/assets_dev --extra-mount $X/mount3 --world mm7 --headless-run-scenario $L/$t.yml --scenario-no-color > final_${t}_$n.log 2>&1
    echo "$t run $n exit $? passed $(grep -c '^PASS' final_${t}_$n.log) of $(grep -o 'steps=[0-9]*' final_${t}_$n.log | head -1) $(grep -E '^Scenario failure' final_${t}_$n.log | head -1)"
  done
done > four.out
