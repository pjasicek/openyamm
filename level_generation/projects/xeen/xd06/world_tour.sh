#!/bin/bash
# world_tour.sh <list.py> <name>: screenshot tour of the map installed in assets_dev, Xeen world (one game; waits on its PID)
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd06; cd $R; mkdir -p $X/$2
python3 $OYR/level_generation/projects/xeen/xd06/tour.py $OYR/level_generation/projects/xeen/xd06/$1 $X/$2.yml $X/$2
"$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated a8xd06$2$RANDOM --binary $R/build-xeen/game/openyamm --world xeen --map xeen_xd06.blv --assets $R/assets_dev --set debug.screenshot_tour_path=$X/$2.yml --warmup 4 --seconds 300 > $X/$2.log 2>&1 &
pid=$!; while kill -0 $pid 2>/dev/null; do sleep 2; done
ls $X/$2 | wc -l; python3 $OYR/level_generation/projects/xeen/xd06/sheet.py $X/$2_sheet.jpg "$X/$2/*.png"
