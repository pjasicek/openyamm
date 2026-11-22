#!/bin/bash
# Lane A7: the map's playtests N times each (default 4), one game at a time, from output/studio_cal/a7/root.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; L=$R/devdocs/xeen/briefs/xd05/L4; ROOT=${ROOT:-$R/assets_dev}
N=${N:-4}; TESTS=${TESTS:-"playtest playtest_back playtest_hostility"}
mkdir -p $R/output/studio_cal/xd05/a7_xrun; cd $R/output/studio_cal/xd05/a7_xrun
for n in $(seq 1 $N); do for t in $TESTS; do
  SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build-xeen/game/openyamm --asset-root $ROOT --world xeen --headless-run-scenario $L/$t.yml --scenario-no-color > ${t}_$n.log 2>&1
  echo "$t run $n exit $? passed $(grep -c '^PASS' ${t}_$n.log) of $(grep -o 'steps=[0-9]*' ${t}_$n.log | head -1) $(grep -E '^Scenario failure' ${t}_$n.log | head -1 | cut -c1-200)"
done; done
