#!/bin/bash
# play.sh <playtest.yml> <name> [count] [map]: the playtest from assets_dev in the Xeen world (--map xeen_xd09.blv, or
# the fourth argument: "none" for no --map, as the way-in test from X5 needs); one game at a time, waits on its PID
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd09; L=$R/devdocs/xeen/briefs/xd09/L4
M=${4:-xeen_xd09.blv}; MAP=(--map $M); [ "$M" = none ] && MAP=()
mkdir -p $X/run/world; cd $X/run/world; S=$(date +%H%M%S)
for n in $(seq 1 ${3:-1}); do
  U=$X/userdata/world_${S}_$2_$n; mkdir -p "$U"
  SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 timeout 1500 $R/build-xeen/game/openyamm --asset-root $R/assets_dev --world xeen "${MAP[@]}" --user-data $U --headless-run-scenario $L/$1 --scenario-no-color > $2_$n.log 2>&1 &
  pid=$!; while kill -0 $pid 2>/dev/null; do sleep 2; done; wait $pid; rc=$?
  echo "$2 run $n exit $rc passed $(grep -c '^PASS' $2_$n.log) of $(grep -o 'steps=[0-9]*' $2_$n.log | head -1)"; grep -E "^(FAIL|Scenario failure)" $2_$n.log | tail -3
done
