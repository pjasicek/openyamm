#!/bin/bash
# xfour.sh: the playtests N times each (default 4), one game process at a time, from assets_dev with the Xeen world.
# --map xeen_xd27.blv (the lair as the initial map); playtest_in starts on X2 (--map xeen_x2.odm).
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd27; L=$R/devdocs/xeen/briefs/xd27/L4
N=${N:-4}; TESTS=${TESTS:-"playtest playtest_fall playtest_hostility playtest_in"}
S=$(date +%H%M%S); mkdir -p $X/xrun/four_$S; cd $X/xrun/four_$S
for n in $(seq 1 $N); do for t in $TESTS; do
  mkdir -p ud_${t}_$n; M=xeen_xd27.blv; [ $t = playtest_in ] && M=xeen_x2.odm
  SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build-xeen/game/openyamm --asset-root $R/assets_dev --world xeen --map $M \
    --user-data $PWD/ud_${t}_$n --headless-run-scenario $L/$t.yml --scenario-no-color > ${t}_$n.log 2>&1 &
  P=$!; wait $P; E=$?
  echo "$t run $n exit $E passed $(grep -c '^PASS' ${t}_$n.log) of $(grep -o 'steps=[0-9]*' ${t}_$n.log | head -1) $(grep -E '^Scenario failure' ${t}_$n.log | head -1 | cut -c1-220)"
done; done
echo "logs: $X/xrun/four_$S"
