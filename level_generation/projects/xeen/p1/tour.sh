#!/bin/bash
# A windowed tour of P1 from the scratch root (through lane A6's game slots). Usage: tour.sh <tour.yml> <name>
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; cd $R
SDL_AUDIODRIVER=dummy level_generation/projects/xeen/common/run/game_slot.sh ./tools/run_game.sh --isolated a6p1_$2_$RANDOM \
  --binary build-xeen/game/openyamm --world xeen --map xeen_p1.blv --assets $R/output/studio_cal/p1/root \
  --set debug.screenshot_tour_path=$R/output/studio_cal/p1/$1 --warmup 4 --seconds 90 > $R/output/studio_cal/p1/$2.log 2>&1 &
P=$!; wait $P; echo "tour exit $?"
