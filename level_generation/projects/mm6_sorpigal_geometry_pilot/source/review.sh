#!/bin/bash
# Build, bake, tour and check one map into its review folder:  source/review.sh <map> <run> [samples]
# (New Sorpigal runs go to review/<run>, the other maps' to review/<map>/<run>; see source/maps.py.)
set -e
cd "$(dirname "$0")/.."
MAP=$1; RUN=$2; SAMPLES=${3:-16}
OUT=$(python3 -c "import sys; sys.path.insert(0, 'source'); import maps; print(maps.run('$MAP', '$RUN'))")
python3 source/build.py --map "$MAP"
python3 source/build.py --map "$MAP" --bake "$SAMPLES"
python3 source/town_tour.py --map "$MAP" "$OUT"
ROOT=$(cd ../../.. && pwd)
"$ROOT/tools/run_game.sh" --isolated "geo_${MAP}_$RUN" --assets "$PWD/playtest/assets_dev" --world mm6 --map "$MAP.odm" \
  --warmup 5 --seconds 600 --set video.weather_quality=off --set debug.screenshot_tour_path="$OUT/tour.yml" > "$OUT/run.log" 2>&1 || true
if [ "$MAP" = oute3 ]; then python3 source/run_checks.py || true; fi
python3 -c "import os; print('lighting bytes', os.path.getsize('playtest/assets_dev/worlds/mm6/maps/$MAP.lighting'))"
