#!/bin/bash
# xfour.sh: the playtests N times each (default 4), one game process at a time, from assets_dev with the Xeen world.
# --map xeen_xd12.blv for the tests that start in the tower (lane A8, 2026-11-20; XD-12 copy of XD-27's); playtest_way_in
# starts on X2 (installed) and runs without --map.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd12; L=$R/devdocs/xeen/briefs/xd12/L4
N=${N:-4}; TESTS=${TESTS:-"playtest playtest_b playtest_hostility playtest_way_in playtest_fall"}
S=$(date +%H%M%S); mkdir -p $X/xrun/four_$S; cd $X/xrun/four_$S
for n in $(seq 1 $N); do for t in $TESTS; do
  mkdir -p ud_${t}_$n; MAPARG="--map xeen_xd12.blv"; [ $t = playtest_way_in ] && MAPARG=
  SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build-xeen/game/openyamm --asset-root $R/assets_dev --world xeen $MAPARG \
    --user-data $PWD/ud_${t}_$n --headless-run-scenario $L/$t.yml --scenario-no-color > ${t}_$n.log 2>&1 &
  P=$!; wait $P; E=$?
  echo "$t run $n exit $E passed $(grep -c '^PASS' ${t}_$n.log) of $(grep -o 'steps=[0-9]*' ${t}_$n.log | head -1) $(grep -E '^Scenario failure' ${t}_$n.log | head -1 | cut -c1-220)"
done; done
echo "logs: $X/xrun/four_$S"
