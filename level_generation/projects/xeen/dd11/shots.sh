#!/bin/bash
# DD-11A/B/C tour pictures from the shared scratch root (one game, waits on its exact PID). shots.sh <key>
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
K=$1
R=$OYR; X=$R/output/studio_cal/$K; T=$X/shots.yml
cd $R
"$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated ${K}shots$RANDOM --binary build-xeen/game/openyamm --world xeen --map xeen_$K.blv \
  --assets $R/output/studio_cal/dd11/root --set debug.screenshot_tour_path=$T --warmup 4 --seconds 200 > $X/shots.log 2>&1 &
pid=$!
while kill -0 $pid 2>/dev/null; do sleep 2; done
echo "done: $(ls $X/shots | wc -l) shots"
