#!/bin/bash
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd05; L=$R/devdocs/xeen/briefs/xd05/L4
mkdir -p $X/run/four; cd $X/run/four
for n in 1 2 3 4; do
 for t in playtest playtest_back; do
  ( "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build/game/openyamm --asset-root ${ROOT:-$X/root} --world mm7 --headless-run-scenario $L/$t.yml --scenario-no-color > ${t}_$n.log 2>&1
    echo "$t run $n exit $? passed $(grep -c '^PASS' ${t}_$n.log) of $(grep -o 'steps=[0-9]*' ${t}_$n.log | head -1)" ) &
 done; wait
done
