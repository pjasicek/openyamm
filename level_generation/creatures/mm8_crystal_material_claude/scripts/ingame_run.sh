#!/usr/bin/env bash
# Run the four comparison tours of one fixture label in sequence (ingame_prepare.py first). Usage: ingame_run.sh <label>
set -u
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/mm8_crystal_material_claude; L=$1
A=$PWD/$P/work/fixture_$L/assets
for run in ${RUNS:-out_dragon out_walker in_dragon in_walker}; do
  case $run in
    out_*) where=(--map oute3.odm --position -3718.493 3245.946 1.0 --yaw-radians 3.359 --pitch-degrees -13.751);;
    in_*) where=(--map 6d19.blv --position 1672.832 -2938.578 -46.896 --yaw-radians 3.132 --pitch-degrees -14.868);;
  esac
  ./tools/run_game.sh --isolated "crystal-$L-$run" --world mm6 "${where[@]}" --assets "$A" \
    --set rendering.item_models=false --set debug.actor_models=true \
    --set debug.actor_models_manifest=worlds/mm8/models/actors.yml --set debug.immortal=true \
    --set debug.menu_input_tour_path=$PWD/$P/review/ingame/$L/$run.yml --warmup 3 --seconds 25 \
    > "$P/review/ingame/$L/$run.log" 2>&1
  echo "$run exit $? $(ls $P/review/ingame/$L/$run 2>/dev/null | tr '\n' ' ')"
done
