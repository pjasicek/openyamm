#!/bin/bash
# XD-26 playtests N times each (default 4), one game at a time, --world xeen from the scratch root.
# Usage: TESTS="playtest playtest_hostility" N=4 four.sh
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; L=$R/devdocs/xeen/briefs/xd26/L4; ROOT=${ROOT:-$R/output/studio_cal/xd26/root}
N=${N:-4}; OUT=$R/output/studio_cal/xd26/run; BIN=$R/build-xeen/game/openyamm; TESTS=${TESTS:-playtest}
mkdir -p $OUT; cd $OUT
for n in $(seq 1 $N); do for t in $TESTS; do
  for try in 1 2 3 4 5; do
    until [ -x $BIN ]; do sleep 10; done
    SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $BIN --asset-root $ROOT --world xeen --headless-run-scenario $L/$t.yml --scenario-no-color > ${t}_$n.log 2>&1
    e=$?; [ $e -eq 126 ] || break; sleep 30
  done
  echo "xd26 $t run $n exit $e passed $(grep -c '^PASS' ${t}_$n.log) of $(grep -o 'steps=[0-9]*' ${t}_$n.log | head -1) $(grep -E '^Scenario failure' ${t}_$n.log | head -1 | cut -c1-300)"
done; done
