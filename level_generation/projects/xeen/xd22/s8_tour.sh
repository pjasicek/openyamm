#!/bin/bash
# s8_tour.sh <before|after> <assets root>: one picture tour, waiting on the exact PID.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
cd "$OYR"; X=output/studio_cal/xd22
"$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated xd22s8$1$RANDOM --binary build-xeen/game/openyamm --world xeen --map xeen_xd22.blv \
  --assets $2 --set debug.screenshot_tour_path=$PWD/$X/s8_$1.yml --warmup 4 --seconds 200 > $X/s8_$1.log 2>&1 &
pid=$!
while kill -0 $pid 2>/dev/null; do sleep 2; done
echo "$1 done: $(ls $X/s8_$1 2>/dev/null | wc -l) shots"
