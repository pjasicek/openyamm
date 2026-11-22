#!/bin/bash
# The playtests N times each (default 4), one game process at a time (exact PIDs), from assets_dev in the Xeen world.
# MAP_<test> overrides --map (the way-in tests start on X5).
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd10; L=$R/devdocs/xeen/briefs/xd10/L4
N=${N:-4}; TESTS=${TESTS:-"playtest playtest_hostility playtest_exit_north playtest_exit_south playtest_in_north playtest_in_south"}
S=$(date +%H%M%S); mkdir -p $X/run/four_$S; cd $X/run/four_$S
for n in $(seq 1 $N); do for t in $TESTS; do
  MAP=xeen_xd10.blv; case $t in playtest_in_*) MAP=xeen_x5.odm;; esac
  mkdir -p ud_${t}_$n
  SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build-xeen/game/openyamm --asset-root $R/assets_dev --world xeen --map $MAP \
    --user-data $PWD/ud_${t}_$n --headless-run-scenario $L/$t.yml --scenario-no-color > ${t}_$n.log 2>&1 &
  P=$!; wait $P; E=$?
  echo "$t run $n exit $E passed $(grep -c '^PASS' ${t}_$n.log) of $(grep -o 'steps=[0-9]*\|/[0-9]* ' ${t}_$n.log | head -1) $(grep -E '^Scenario failure' ${t}_$n.log | head -1 | cut -c1-300)"
done; done
echo "logs: $X/run/four_$S"
