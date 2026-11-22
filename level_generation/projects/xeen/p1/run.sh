#!/bin/bash
# run.sh: P1's playtests N times each (default 1), headless, each game run through lane A6's game slots.
# ASSETS: the asset root (absolute; default the scratch root); TESTS: the list.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/p1; L=$R/devdocs/xeen/briefs/p1/L4
N=${N:-1}
TESTS=${TESTS:-"playtest playtest_hostility playtest_lava playtest_test playtest_bypass playtest_way_up playtest_way_up_column playtest_sleeper playtest_daily"}
ASSETS=${ASSETS:-$X/root}
S=$(date +%H%M%S); mkdir -p $X/xrun/run_$S; cd $X/xrun/run_$S
for n in $(seq 1 $N); do for t in $TESTS; do
  mkdir -p ud_${t}_$n
  SDL_AUDIODRIVER=dummy $R/level_generation/projects/xeen/common/run/game_slot.sh timeout 1800 $R/build-xeen/game/openyamm \
    --asset-root $ASSETS --world xeen --map xeen_p1.blv --user-data $PWD/ud_${t}_$n \
    --headless-run-scenario $L/$t.yml --scenario-no-color > ${t}_$n.log 2>&1 &
  P=$!; wait $P; E=$?
  echo "$t run $n exit $E passed $(grep -c '^PASS' ${t}_$n.log) of $(grep -o 'steps=[0-9]*' ${t}_$n.log | head -1) $(grep -E '^Scenario failure|FAIL' ${t}_$n.log | head -1 | cut -c1-300)"
done; done
echo "logs: $X/xrun/run_$S"
