#!/usr/bin/env bash
# S3: builds the shapes gallery (examples/shapes_gallery: a bent hall, a path corridor, stairs, a ramp, a cave, a
# pillar and a dais), mounts it over assets_dev and walks through every shape in the game. The scenario asserts
# the party's height on the dais, half way up the steps, in the gallery, half way down the ramp and in the cave.
# With --shots also renders the plan and the iso view and takes the in-game tour (examples/shapes_gallery/tour.yml)
# into output/studio_shapes/.
set -euo pipefail
studio="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd "$studio/.." && pwd)"
oymap="$studio/build/oymap"
project="$studio/examples/shapes_gallery"
run="$repo/output/studio_shapes"
mkdir -p "$run"
"$oymap" fmt "$project" --check
"$oymap" build "$project" --assets "$repo/assets_dev"
"$oymap" install "$project" --mount "$run/mount" --assets "$repo/assets_dev" > /dev/null
(cd "$run" && "$repo/build/game/openyamm" --asset-root "$repo/assets_dev" --extra-mount "$run/mount" --world mm6 \
    --headless-run-scenario "$project/playtest.yml" --scenario-no-color > "$run/walk.log" 2>&1) || true
grep -E "^(FAIL|ASSERT fail|Scenario)" "$run/walk.log"
grep -q "^Scenario passed" "$run/walk.log"
"$oymap" audit studio02.blv --world mm6 --assets "$repo/assets_dev" --mount "$run/mount" --reach | grep -E "^(error|warning)" \
    && { echo "the built map has findings"; exit 1; } || echo "audit of the built map: no errors or warnings"
# The closet's hinged door must shut it off until its event (and the panel room's door the four rooms behind it): the
# walk alone would also pass with a leaf that blocks nothing.
"$oymap" solve "$project" --assets "$repo/assets_dev" | grep -q "^step 1: 29 sectors (63 of 72)" \
    || { echo "the closet is not closed off by its hinged door"; exit 1; }
echo "solve: the closet opens only with its door"
if [ "${1:-}" = "--shots" ]; then
    # In-game views need an asset root of their own (the desktop launcher takes no mount): a hard-link copy.
    root="$repo/output/studio_slice_root"
    [ -d "$root" ] || cp -al "$repo/assets_dev" "$root"
    "$oymap" install "$project" --root "$root" > /dev/null
    sed "s|@OUTPUT@|$run/shots|" "$project/tour.yml" > "$run/tour.yml"
    mkdir -p "$run/shots"
    "$repo/tools/run_game.sh" --isolated studioshapes --world mm6 --map studio02.blv --assets "$root" \
        --warmup 5 --seconds 310 --set "debug.screenshot_tour_path=$run/tour.yml" | tail -1
    for view in plan iso; do
        "$oymap" render studio02.blv --world mm6 --assets "$repo/assets_dev" --mount "$run/mount" \
            --out "$run/$view.png" --view "$view" --size 1024
    done
fi
