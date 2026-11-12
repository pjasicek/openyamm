#!/bin/bash
# The silhouette-kit prototype on one map: build with the kit on the given BModels, bake, and capture the kit tour
# on the result and on the re-baked unchanged map.   source/kit_run.sh <map> <models> <shot>...
set -e
cd "$(dirname "$0")/.."
MAP=$1; MODELS=$2; shift 2
OUT=review/kit/$MAP
python3 source/build.py --map "$MAP" --kit "$MODELS"
python3 source/build.py --map "$MAP" --bake 64
python3 source/kit_tour.py "$MAP" "$OUT/kit" "$@"
python3 source/kit_tour.py "$MAP" "$OUT/now" "$@"
ROOT=$(cd ../../.. && pwd)
"$ROOT/tools/run_game.sh" --isolated "geo_kit_$MAP" --assets "$PWD/playtest/assets_dev" --world mm6 --map "$MAP.odm" \
  --warmup 5 --seconds 300 --set video.weather_quality=off --set debug.screenshot_tour_path="$PWD/$OUT/kit/tour.yml" \
  > "$OUT/kit/run.log" 2>&1 || true
"$ROOT/tools/run_game.sh" --isolated "geo_kitnow_$MAP" --assets "$PWD/playtest/rebake/assets_dev" --world mm6 \
  --map "$MAP.odm" --warmup 5 --seconds 300 --set video.weather_quality=off \
  --set debug.screenshot_tour_path="$PWD/$OUT/now/tour.yml" > "$OUT/now/run.log" 2>&1 || true
python3 -c "import json; p=json.load(open('build/$MAP/plan.json')); print('$MAP', [(b['model_name'], b['new_triangles']) for b in p['buildings']])"
