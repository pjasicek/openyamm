#!/bin/bash
# A6: take a tour (tools/tour.py set) and a
# contact sheet. Usage: look.sh <tour set> <label>
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
set -e
cd "$OYR"
C=output/studio_cal/d2
O=openyamm-studio/build-xeen/oymap
$O export $C/build/xeen_d2.odm --out $C/build/export.json > /dev/null
mkdir -p $C/tour/$2
python3 $OYR/level_generation/projects/xeen/d4/tour.py $C/build $PWD/$C/tour/$2 $PWD/$C/tour_$2.yml $1
"$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated d2tour_$2 --world xeen --map xeen_d2.odm --binary build-xeen/game/openyamm \
  --assets ${D2_ASSETS:-$PWD/assets_dev} --warmup 3 --seconds 170 \
  --set debug.screenshot_tour_path=$PWD/$C/tour_$2.yml > $C/run/tour_$2.log 2>&1
python3 $OYR/level_generation/projects/xeen/d4/sheet.py $C/tour/$2 $C/pics/sheet_$2.jpg 3 640
echo done
