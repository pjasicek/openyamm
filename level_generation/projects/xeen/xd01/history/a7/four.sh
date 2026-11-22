#!/bin/bash
# Phase 0 (lane A7): the map's playtests N times each (default 4) from the lane root, one game at a time.
# four.sh [runs] [test ...]   e.g. four.sh 1 playtest
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../../.." && pwd)"
ROOT=$R/output/studio_cal/a7/root_tower
L=$R/devdocs/xeen/briefs/xd01/L4
N=${1:-4}; shift
TESTS=${@:-playtest playtest_perception playtest_hostility}
cd $R/output/studio_cal/xd01/run
for t in $TESTS; do
for n in $(seq 1 $N); do
  SDL_AUDIODRIVER=dummy timeout 1500 $R/build-xeen/game/openyamm --asset-root $ROOT --world mm7 --headless-run-scenario $L/$t.yml --scenario-no-color > a7_${t}_$n.log 2>&1
  echo "$t run $n exit $? passed $(grep -c '^PASS' a7_${t}_$n.log) $(grep -o 'steps=[0-9]*' a7_${t}_$n.log | head -1) $(grep -E '^Scenario failure|FAIL' a7_${t}_$n.log | head -1)"
done; done
