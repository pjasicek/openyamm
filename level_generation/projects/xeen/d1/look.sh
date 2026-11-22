#!/bin/bash
# A6: install the current build into assets_dev, write the terrain weights and take a tour into a new folder.
# Usage: look.sh <tour set> <label>   (the label must be new: old tour folders are deleted by hand)
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
set -e
cd "$OYR"
C=output/studio_cal/d1
O=openyamm-studio/build-xeen/oymap
$O install devdocs/xeen/briefs/d1/L4 --build $C/build --root assets_dev > $C/run/install.log
python3 tools/terrain_materials.py weights --world xeen --map xeen_d1.odm > $C/run/weights.log
$O export $C/build/xeen_d1.odm --out $C/build/export.json > /dev/null
mkdir -p $C/tour/$2
python3 $OYR/level_generation/projects/xeen/d1/tour.py $C/build $PWD/$C/tour/$2 $PWD/$C/tour_$2.yml $1
"$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated d1tour_$2 --world xeen --map xeen_d1.odm --binary build-xeen/game/openyamm \
  --assets $PWD/assets_dev --warmup 3 --seconds 200 \
  --set debug.screenshot_tour_path=$PWD/$C/tour_$2.yml > $C/run/tour_$2.log 2>&1
python3 $OYR/level_generation/projects/xeen/d1/sheet.py $C/tour/$2 $C/pics/sheet_$2.jpg 4 480
echo done
