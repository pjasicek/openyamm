#!/usr/bin/env bash
# Runs the review tour <name> on the native BLV and (with --original) on the old map, in parallel; waits on both PIDs.
# Usage: run_tours.sh <name> [--original] [extra --set args for the BLV run...]
set -u
cd "$(dirname "$0")/../../.."
P=level_generation/projects/mm9r_bathhouse
NAME=$1; shift
ORIG=0
if [ "${1:-}" = "--original" ]; then ORIG=1; shift; fi
START=$(python3 -c "import yaml;t=yaml.safe_load(open('$P/review_tour_$NAME.yml'));p=t['shots'][0]['position'];print(*p)")
N=$(python3 -c "import yaml;print(len(yaml.safe_load(open('$P/review_tour_$NAME.yml'))['shots']))")
SECS=$((N * 3 + 30))
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated bathhouse_$NAME --world mm9 --map bathhouse.blv --assets "$PWD/output/mm9_rework/assets_dev" \
    --position $START --yaw-radians 0 --pitch-degrees 0 --warmup 3 --seconds $SECS \
    --set debug.screenshot_tour_path=$PWD/$P/review_tour_$NAME.yml "$@" > $P/work/tour_$NAME.log 2>&1 &
A=$!
B=
if [ $ORIG = 1 ]; then
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated bathhouse_${NAME}_o --world mm9 --map bathhouse.odm \
    --assets "$PWD/output/mm9_rework/assets_original" --position $START --yaw-radians 0 --pitch-degrees 0 --warmup 3 \
    --seconds $SECS --set video.view_distance=unlimited \
    --set debug.screenshot_tour_path=$PWD/$P/review_tour_${NAME}_original.yml > $P/work/tour_${NAME}_o.log 2>&1 &
B=$!
fi
while kill -0 $A 2>/dev/null || { [ -n "$B" ] && kill -0 $B 2>/dev/null; }; do sleep 2; done
tail -2 $P/work/tour_$NAME.log
ls $P/review/$NAME | wc -l
