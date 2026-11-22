#!/bin/bash
# DD-02's playtests N times each (default 4), one game process at a time, --world xeen --map xeen_dd02.blv.
# ASSETS defaults to the scratch root; the lane lead reruns from assets_dev with ASSETS=$PWD/assets_dev.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/dd02; L=$R/devdocs/xeen/briefs/dd02/L4
ASSETS=${ASSETS:-$X/root}; N=${N:-4}; TESTS=${TESTS:-"playtest playtest_b playtest_hostility playtest_exit"}
S=$(date +%H%M%S); mkdir -p $X/run/four_$S; cd $X/run/four_$S
for n in $(seq 1 $N); do for t in $TESTS; do
  mkdir -p ud_${t}_$n
  SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build-xeen/game/openyamm --asset-root $ASSETS --world xeen --map xeen_dd02.blv \
    --user-data $PWD/ud_${t}_$n --headless-run-scenario $L/$t.yml --scenario-no-color > ${t}_$n.log 2>&1 &
  P=$!; wait $P; E=$?
  echo "$t run $n exit $E passed $(grep -c '^PASS' ${t}_$n.log) of $(grep -o 'steps=[0-9]*' ${t}_$n.log | head -1) $(grep -E '^Scenario failure' ${t}_$n.log | head -1 | cut -c1-300)"
done; done
echo "logs: $X/run/four_$S"
