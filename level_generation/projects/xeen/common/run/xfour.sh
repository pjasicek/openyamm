#!/bin/bash
# Lane A7 move: a map's playtests N times each (default 4), one game at a time, --world xeen from root_xgame.
# Usage: KEY=xd02 TESTS="playtest playtest_hostility" N=4 level_generation/projects/xeen/common/run/xfour.sh
# A run that exits 126 (A1 relinking build-xeen under it) is retried after the binary is executable again.
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../.." && pwd)"; L=$R/devdocs/xeen/briefs/$KEY/L4; ROOT=${ROOT:-$R/assets_dev}
N=${N:-4}; OUT=$R/output/studio_cal/$KEY/a7_xrun; BIN=$R/build-xeen/game/openyamm
mkdir -p $OUT; cd $OUT
for n in $(seq 1 $N); do for t in $TESTS; do
  for try in 1 2 3 4 5; do
    until [ -x $BIN ]; do sleep 10; done
    # at most two games in the lane: take a free slot of two (output/studio_cal/a7/locks/game{1,2}.lock)
    mkdir -p $R/output/studio_cal/a7/locks
    while :; do
      for slot in 1 2; do
        flock -n $R/output/studio_cal/a7/locks/game$slot.lock -c "SDL_AUDIODRIVER=dummy $R/tools/heavy.sh 6 timeout 1500 $BIN --asset-root $ROOT --world xeen --headless-run-scenario $L/$t.yml --scenario-no-color > ${t}_$n.log 2>&1; echo \$? > ${t}_$n.exit" && break 2
      done
      sleep 5
    done
    e=$(cat ${t}_$n.exit); [ $e -eq 126 ] || break; sleep 30
  done
  echo "$KEY $t run $n exit $e passed $(grep -c '^PASS' ${t}_$n.log) of $(grep -o 'steps=[0-9]*' ${t}_$n.log | head -1) $(grep -E '^Scenario failure' ${t}_$n.log | head -1 | cut -c1-300)"
done; done
