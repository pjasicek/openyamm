#!/bin/bash
# The fair "before" of a map: re-bake the unchanged map with today's tool and capture every review pose of it.
#   source/original.sh <map> [--no-bake]     (--no-bake: capture again from the existing re-bake)
set -e
cd "$(dirname "$0")/.."
MAP=$1
OUT=$(python3 -c "import sys; sys.path.insert(0, 'source'); import maps; print(maps.original('$MAP'))")
if [ "$2" != --no-bake ]; then python3 source/build.py --map "$MAP" --original; fi
python3 source/town_tour.py --map "$MAP" "$OUT"
ROOT=$(cd ../../.. && pwd)
"$ROOT/tools/run_game.sh" --isolated "geo_${MAP}_original" --assets "$PWD/playtest/rebake/assets_dev" --world mm6 \
  --map "$MAP.odm" --warmup 5 --seconds 600 --set video.weather_quality=off --set debug.screenshot_tour_path="$OUT/tour.yml" > "$OUT/run.log" 2>&1 || true
ls "$OUT" | grep -c png
