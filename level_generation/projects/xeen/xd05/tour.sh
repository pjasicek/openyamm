#!/bin/bash
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd05; cd $R; mkdir -p $X/$2
python3 $OYR/level_generation/projects/xeen/xd05/history/tools/tour.py $X/$1 $X/$2.yml $X/$2
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated xd05tour$RANDOM --world mm7 --map xeen_xd05.blv --assets ${3:-$X/root} --set debug.screenshot_tour_path=$X/$2.yml --warmup 4 --seconds 400 > $X/$2.log 2>&1
ls $X/$2 | wc -l; python3 $X/sheet.py $X/$2_sheet.jpg "$X/$2/*.png"
