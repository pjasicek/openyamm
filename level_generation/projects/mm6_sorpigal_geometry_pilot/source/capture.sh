#!/bin/bash
# Capture the tour for the original map and the stage: source/capture.sh <name> [extra game args...]
# Writes review/original and review/<name>, and side-by-side sheets in review/cmp_<name>.
set -e
cd "$(dirname "$0")/../../../.."
P=$PWD/level_generation/projects/mm6_sorpigal_geometry_pilot
name=$1; shift
mkdir -p "$P/review/original" "$P/review/$name"
python3 "$P/source/tour.py" "$P/review/original"
python3 "$P/source/tour.py" "$P/review/$name"
./tools/run_game.sh --isolated geo_original --world mm6 --map oute3.odm --warmup 3 --seconds 90 \
    --set debug.screenshot_tour_path="$P/review/original/tour.yml" "$@" > "$P/review/original/run.log" 2>&1 &
./tools/run_game.sh --isolated "geo_$name" --assets "$P/playtest/assets_dev" --world mm6 --map oute3.odm --warmup 3 \
    --seconds 90 --set debug.screenshot_tour_path="$P/review/$name/tour.yml" "$@" > "$P/review/$name/run.log" 2>&1 &
wait
python3 "$P/source/compare.py" "$P/review/original" "$P/review/$name" "$P/review/cmp_$name"
