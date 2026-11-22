#!/bin/bash
# DD-17's playtests N times each (default 4), one game process at a time (exact PIDs), from ASSETS (default the scratch
# root output/studio_cal/dd17/root; the lane lead reruns with ASSETS=$PWD/assets_dev) in the Xeen world. TESTS= picks.
# Every game run goes through the lane's slot wrapper (level_generation/projects/xeen/common/run/game_slot.sh).
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/dd17; L=$R/devdocs/xeen/briefs/dd17/L4
ASSETS=${ASSETS:-$X/root}
N=${N:-4}; TESTS=${TESTS:-"playtest playtest_dials playtest_hatch playtest_refused playtest_exit playtest_hostility playtest_belt"}
S=$(date +%H%M%S); mkdir -p $X/run/four_$S; cd $X/run/four_$S
for n in $(seq 1 $N); do for t in $TESTS; do
  mkdir -p ud_${t}_$n
  SDL_AUDIODRIVER=dummy timeout 1500 $R/level_generation/projects/xeen/common/run/game_slot.sh $R/build-xeen/game/openyamm --asset-root $ASSETS \
    --world xeen --map xeen_dd17.blv --user-data $PWD/ud_${t}_$n --headless-run-scenario $L/$t.yml --scenario-no-color \
    > ${t}_$n.log 2>&1 &
  P=$!; wait $P; E=$?
  echo "$t run $n exit $E steps $(grep -o 'steps=[0-9]*' ${t}_$n.log | head -1) $(grep -cE '^PASS' ${t}_$n.log) PASS; $(grep -iE 'failure|FAIL' ${t}_$n.log | head -2 | cut -c1-400)"
done; done
echo "logs: $X/run/four_$S"
