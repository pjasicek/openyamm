#!/bin/bash
# Take a tour on an asset root: tour.sh <xd0N> <tour.yml> <asset root> <log>
R=/home/pjasicek/github/OpenYAMM
cd $R
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated "xtex_$1_$RANDOM" --world mm7 --map xeen_$1.blv --assets "$3" --set debug.screenshot_tour_path="$2" --warmup 4 --seconds 300 > "$4" 2>&1
echo "tour $1 exit $?"
