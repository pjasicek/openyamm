#!/bin/bash
# shoot.sh <tour name>: one tour run from the scratch root (one game process; waits on its exact PID).
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/dd12; T=$1; shift
cd $R
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated a8-dd12-$T --binary build-xeen/game/openyamm --assets ${ASSETS:-$X/root} \
  --world xeen --map xeen_dd12.blv --warmup 3 --seconds ${SECS:-150} \
  --set debug.screenshot_tour_path=$X/shots/$T.yml "$@" > $X/shots/$T.log 2>&1 &
P=$!; wait $P; echo "exit $? ; $(ls $X/shots/$T 2>/dev/null | wc -l) shots"
