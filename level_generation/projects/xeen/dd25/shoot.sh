#!/bin/bash
# shoot.sh <tour name>: one tour run (shots/<tour>.yml) from ASSETS (default the scratch root), through the session's
# game lock and slot; one game process, waits on its exact PID; then JPEG sheets shots/<tour>_N.jpg.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/dd25; T=$1; shift
cd $R
SDL_AUDIODRIVER=dummy flock $R/output/studio_cal/a8_s13/game.lock $R/level_generation/projects/xeen/common/run/game_slot.sh \
  "$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated a8-dd25-$T --binary build-xeen/game/openyamm --assets ${ASSETS:-$X/root} \
  --world xeen --map xeen_dd25.blv --warmup 3 --seconds ${SECS:-120} \
  --set debug.screenshot_tour_path=$X/shots/$T.yml "$@" > $X/shots/$T.log 2>&1 &
P=$!; wait $P; echo "exit $? ; $(ls $X/shots/$T 2>/dev/null | wc -l) shots"
python3 $OYR/level_generation/projects/xeen/dd25/sheet.py $X/shots/$T $X/shots/$T
