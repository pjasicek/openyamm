#!/bin/bash
# tour.sh <tour.yml> <log> [root]: one screenshot tour in the game from the given root (default this pass's root).
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../../.." && pwd)"
X=$R/output/studio_cal/xd03/pass2
ROOT=${3:-$X/root}
cd $R
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated xd03p2tour$RANDOM --world mm7 --map xeen_xd03.blv --assets $ROOT --set debug.screenshot_tour_path=$1 --warmup 4 --seconds 300 > $2 2>&1
echo "tour exit $?"
