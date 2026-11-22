#!/bin/bash
# tour.sh <shots.py> <name>: a screenshot tour of the scratch mount
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd06; cd $R; mkdir -p $X/$2
python3 $R/output/studio_cal/xd05/tools/tour.py $OYR/level_generation/projects/xeen/xd06/$1 $X/$2.yml $X/$2
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated xd06tour$RANDOM --world mm7 --map xeen_xd06.blv --assets $R/output/studio_play/xeen_root --extra-mount $X/mount --set debug.screenshot_tour_path=$X/$2.yml --warmup 4 --seconds 420 > $X/$2.log 2>&1
ls $X/$2 | wc -l; python3 $R/output/studio_cal/xd05/sheet.py $X/$2_sheet.jpg "$X/$2/*.png"
