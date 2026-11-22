#!/bin/bash
# XD-23 tour pictures from the scratch root (one game, waits on its exact PID). Usage: shots.sh [tour.yml] [name]
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd23; T=${1:-$X/shots.yml}; N=${2:-xd23shots}
cd $R
"$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated $N$RANDOM --binary build-xeen/game/openyamm --world xeen --map xeen_xd23.blv \
  --assets $X/root --set debug.screenshot_tour_path=$T --warmup 4 --seconds 200 > $X/$N.log 2>&1 &
pid=$!
while kill -0 $pid 2>/dev/null; do sleep 2; done
echo "done: $(ls $X/shots | wc -l) shots"
