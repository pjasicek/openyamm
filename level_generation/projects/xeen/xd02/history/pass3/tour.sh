#!/bin/bash
# Pass 3: a tour on this pass's private root. Usage: tour.sh <tour.yml> <run name> [seconds]
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../../.." && pwd)"
X=$R/output/studio_cal/xd02/pass3
cd $R
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated "$2" --world mm7 --map xeen_xd02.blv --assets $X/root --warmup 3 --seconds ${3:-240} --set debug.screenshot_tour_path=$1
