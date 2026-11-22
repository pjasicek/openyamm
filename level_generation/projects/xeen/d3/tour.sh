#!/bin/bash
# A5 (2026-11-20, eighth session): D3's tour from assets_dev in one of lane A5's game slots.
#   tour.sh <name> [asset root]    (default assets_dev; writes tour/<name>/ from tour/tour_d3.yml, made by tools/gen_tour.py first)
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
cd "$OYR"
n=$1
python3 level_generation/projects/xeen/d3/gen_tour.py $OYR/output/studio_cal/d3/tour/$n > /dev/null
mkdir -p output/studio_cal/d3/tour/$n
level_generation/projects/xeen/common/run/game_slot.sh ./tools/run_game.sh --isolated a5d3-$n --binary build-xeen/game/openyamm \
  --assets ${2:-assets_dev} --world xeen --map xeen_d3.odm --warmup 4 --seconds 150 \
  --set debug.screenshot_tour_path=$OYR/output/studio_cal/d3/tour/tour_d3.yml \
  > output/studio_cal/d3/tour/$n.log 2>&1
echo "exit $?" >> output/studio_cal/d3/tour/$n.log
