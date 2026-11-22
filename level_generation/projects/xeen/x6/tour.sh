#!/bin/bash
# A5 (2026-11-20): X6's tour in one of lane A5's game slots.
#   tour.sh <name> [asset root]    (default assets_dev; the scratch root is output/studio_cal/x6/root)
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
cd "$OYR"
n=$1
python3 level_generation/projects/xeen/x6/gen_tour.py $OYR/output/studio_cal/x6/tour/$n > /dev/null
mkdir -p output/studio_cal/x6/tour/$n
level_generation/projects/xeen/common/run/game_slot.sh ./tools/run_game.sh --isolated a5x6-$n --binary build-xeen/game/openyamm \
  --assets ${2:-assets_dev} --world xeen --map xeen_x6.odm --warmup 4 --seconds ${TOUR_SECONDS:-170} \
  --set debug.screenshot_tour_path=$OYR/output/studio_cal/x6/tour/tour_x6.yml \
  > output/studio_cal/x6/tour/$n.log 2>&1
echo "exit $?" >> output/studio_cal/x6/tour/$n.log
