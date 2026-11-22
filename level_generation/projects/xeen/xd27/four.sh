#!/bin/bash
# four.sh: both playtests four times each (two game processes at a time), from the play mount
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd27; L=$R/devdocs/xeen/briefs/xd27/L4
S=$(date +%H%M%S); mkdir -p $X/run/four_$S; cd $X/run/four_$S
for n in 1 2 3 4; do
 for t in playtest playtest_fall; do
  ( mkdir -p ud_${t}_$n
    SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build/game/openyamm --asset-root $R/output/studio_play/xeen_root --extra-mount $X/${MOUNT:-mount_play} --world mm7 --user-data $PWD/ud_${t}_$n --headless-run-scenario $L/$t.yml --scenario-no-color > ${t}_$n.log 2>&1
    echo "$t run $n exit $? passed $(grep -c '^PASS' ${t}_$n.log) of $(grep -o 'steps=[0-9]*' ${t}_$n.log | head -1)"; grep -E "^Scenario failure" ${t}_$n.log | head -2 ) &
 done; wait
done
echo "logs: $X/run/four_$S"
