#!/bin/bash
# A6: install the current build into assets_dev, write the terrain weights, refresh the rows mount and take a tour.
# Usage: look.sh <tour set> <label>
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
set -e
cd "$OYR"
C=output/studio_cal/x5
O=openyamm-studio/build-xeen/oymap
$O install devdocs/xeen/briefs/x5/L4 --build $C/build --root assets_dev > $C/run/install.log
python3 tools/terrain_materials.py weights --world xeen --map xeen_x5.odm > $C/run/weights.log
$O install devdocs/xeen/briefs/x5/L4 --build $C/build --mount $C/mount --assets assets_dev > /dev/null
cp $C/mount/engine/data_tables/map_stats.txt $C/mount/engine/data_tables/bolster_maps.txt $C/rows/engine/data_tables/
python3 $OYR/level_generation/projects/xeen/x5/view.py $C/build $C/pics/height.png > /dev/null
mkdir -p $C/tour/$2
python3 $OYR/level_generation/projects/xeen/x5/tour.py $C/build $PWD/$C/tour/$2 $PWD/$C/tour_$2.yml $1
EXTRA=""
grep -q '^9103' assets_dev/worlds/xeen/data_tables/map_stats.txt || EXTRA="--extra-mount $PWD/$C/rows"
"$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated x5tour_$2 --world xeen --map xeen_x5.odm --binary build-xeen/game/openyamm \
  --assets $PWD/assets_dev $EXTRA --warmup 3 --seconds 150 \
  --set debug.screenshot_tour_path=$PWD/$C/tour_$2.yml > $C/run/tour_$2.log 2>&1
python3 $OYR/level_generation/projects/xeen/x5/sheet.py $C/tour/$2 $C/pics/sheet_$2.jpg 4 480
echo done
