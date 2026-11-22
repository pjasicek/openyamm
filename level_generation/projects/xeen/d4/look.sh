#!/bin/bash
# A6 D4: a screenshot tour (tools/tour.py set) of the build in an asset root (default the pre-test stage), one game at a
# time under the lane's second slot, and a contact sheet. Usage: look.sh <tour set> <label> [asset root]
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
set -e
cd "$OYR"
C=output/studio_cal/d4
ROOT=${3:-$PWD/$C/stage/assets_dev}
O=openyamm-studio/build-xeen/oymap
$O export $C/build/xeen_d4.odm --out $C/build/export.json > /dev/null
mkdir -p $C/tour/$2
python3 $OYR/level_generation/projects/xeen/d4/tour.py $C/build $PWD/$C/tour/$2 $PWD/$C/tour_$2.yml $1
EXTRA=""
grep -q '^9111' $ROOT/worlds/xeen/data_tables/map_stats.txt || EXTRA="--extra-mount $PWD/$C/rows"
flock output/studio_cal/a6/locks/game2.lock "$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated d4tour_$2 --world xeen --map xeen_d4.odm \
  --binary build-xeen/game/openyamm --assets $ROOT $EXTRA --warmup 3 --seconds 240 \
  --set debug.screenshot_tour_path=$PWD/$C/tour_$2.yml ${LOOK_SET:-} > $C/run/tour_$2.log 2>&1
python3 $OYR/level_generation/projects/xeen/d4/sheet.py $C/tour/$2 $C/pics/sheet_$2.jpg 4 480
echo done
