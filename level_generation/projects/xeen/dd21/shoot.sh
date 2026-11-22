#!/bin/bash
# shoot.sh <tour name>: one tour run (shots/<name>.yml) from the scratch root, or ASSETS=<root> (the lead's baked
# assets_dev); one game process, through the session's lock and slot wrapper; waits on its exact PID.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/dd21; T=$1; shift
LOCK=${LOCK-$R/output/studio_cal/a8_s13/game.lock}; SLOT=$R/level_generation/projects/xeen/common/run/game_slot.sh
if [ -n "$LOCK" ]; then W=(flock $LOCK $SLOT); else W=(); fi
cd $R
SDL_AUDIODRIVER=dummy "${W[@]}" "$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated a8-dd21-$T --binary build-xeen/game/openyamm \
  --assets ${ASSETS:-$X/root} --world xeen --map xeen_dd21.blv --warmup 3 --seconds ${SECS:-150} \
  --set debug.screenshot_tour_path=$X/shots/$T.yml "$@" > $X/shots/$T.log 2>&1 &
P=$!; wait $P; echo "exit $? ; $(ls $X/shots/$T 2>/dev/null | wc -l) shots"
python3 $OYR/level_generation/projects/xeen/dd21/sheet.py $X/shots/$T $X/shots/$T
