#!/bin/bash
# Take a tour on an asset root: tour.sh <tour.yml> <asset root> <log>
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../../.." && pwd)"
cd $R
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated "xd04p2_$RANDOM" --world mm7 --map xeen_xd04.blv --assets "$2" --set debug.screenshot_tour_path="$1" --warmup 4 --seconds 240 > "$3" 2>&1
echo "tour exit $?"
