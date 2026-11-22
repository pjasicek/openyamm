#!/bin/bash
# A5 (2026-11-20): X7's tour in one of lane A5's game slots.
#   tour.sh <name> [asset root]    (default the scratch root output/studio_cal/x7/root; assets_dev once installed)
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
cd "$OYR"
n=$1
python3 level_generation/projects/xeen/x7/gen_tour.py $OYR/output/studio_cal/x7/tour/$n > /dev/null
mkdir -p output/studio_cal/x7/tour/$n
level_generation/projects/xeen/common/run/game_slot.sh ./tools/run_game.sh --isolated a5x7-$n --binary build-xeen/game/openyamm \
  --assets ${2:-output/studio_cal/x7/root} --world xeen --map xeen_x7.odm --warmup 4 --seconds ${TOUR_SECONDS:-170} \
  --set debug.screenshot_tour_path=$OYR/output/studio_cal/x7/tour/tour_x7.yml \
  > output/studio_cal/x7/tour/$n.log 2>&1
echo "exit $?" >> output/studio_cal/x7/tour/$n.log
