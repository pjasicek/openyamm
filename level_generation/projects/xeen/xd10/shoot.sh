#!/bin/bash
# shoot.sh <tour name> [extra run_game args]: one tour run (one game process; waits on its exact PID).
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd10; T=$1; shift
cd $R
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated xd10_$T --binary build-xeen/game/openyamm --assets $R/assets_dev \
  --world xeen --map xeen_xd10.blv --warmup 3 --seconds ${SECS:-90} \
  --set debug.screenshot_tour_path=$X/shots/$T.yml "$@" > $X/shots/$T.log 2>&1 &
P=$!; wait $P; echo "exit $? ; $(ls $X/shots/$T 2>/dev/null | wc -l) shots"
