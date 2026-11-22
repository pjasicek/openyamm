#!/bin/bash
# shoot.sh <tour name>: one tour run (shots/<name>.yml, from tools/tour.py) from ASSETS (default the scratch root;
# the lane lead: ASSETS=$PWD/assets_dev for the baked tour), one game process (exact PID), inside the lane's slot.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/dd15; T=$1; shift
cd $R
SDL_AUDIODRIVER=dummy $R/level_generation/projects/xeen/common/run/game_slot.sh ./tools/run_game.sh --isolated a8-dd15-$T --binary build-xeen/game/openyamm \
  --assets ${ASSETS:-$X/root} --world xeen --map xeen_dd15.blv --warmup 3 --seconds ${SECS:-200} \
  --set debug.screenshot_tour_path=$X/shots/$T.yml "$@" > $X/shots/$T.log 2>&1 &
P=$!; wait $P; echo "exit $? ; $(ls $X/shots/$T 2>/dev/null | wc -l) shots"
