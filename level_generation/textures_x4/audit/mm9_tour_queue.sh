#!/usr/bin/env bash
# Run screenshot tours sequentially: mm9_tour_queue.sh SHOT_ROOT MAP [MAP...]; each MAP has SHOT_ROOT/MAP/tour.yml.
# ASSETS=<root> overrides the asset root (default: the review root; output/textures_x4_runs/mm9-native for 1x).
set -u
cd "$(dirname "$0")/../../.."
assets=${ASSETS:-$PWD/output/mm9_rework/assets_dev}
root=$1; shift
for map in "$@"; do
    SDL_AUDIODRIVER=dummy timeout 700 ./tools/run_game.sh --isolated "tex9_${map}_$(basename "$root")" --world mm9 --map "${map}.blv" \
        --assets "$assets" --warmup 3 --seconds 600 \
        --set video.view_distance=unlimited --set debug.screenshot_tour_path="$root/$map/tour.yml" > "$root/$map/run.log" 2>&1
    echo "$map $(ls "$root/$map"/*.png 2>/dev/null | wc -l) shots"
done
