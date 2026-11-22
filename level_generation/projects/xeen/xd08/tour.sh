#!/bin/bash
# tour.sh <name>: one tour (output/studio_cal/xd08/<name>.yml) from the scratch root, waiting on the exact PID.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
cd "$OYR"; X=output/studio_cal/xd08
"$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated xd08$1 --binary build-xeen/game/openyamm --world xeen --map xeen_xd08.blv \
  --assets $PWD/$X/root --set debug.screenshot_tour_path=$PWD/$X/$1.yml --warmup 4 --seconds 150 > $X/$1.log 2>&1 &
pid=$!
while kill -0 $pid 2>/dev/null; do sleep 2; done
echo "$1 done: $(ls $X/$1 | wc -l) shots"
