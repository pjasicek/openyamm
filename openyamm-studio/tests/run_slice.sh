#!/usr/bin/env bash
# S0 acceptance: builds the slice dungeon (examples/gatehouse_cellars), installs it into a scratch asset root (a
# hard-link copy of assets_dev under output/, made on first use) and walks it start to goal in the game, headless.
# Usage: tests/run_slice.sh [--shots]   (--shots also captures the screenshot tour into output/studio_slice_shots)
set -euo pipefail
studio="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd "$studio/.." && pwd)"
project="$studio/examples/gatehouse_cellars"
root="$repo/output/studio_slice_root"
run="$repo/output/studio_slice_run"
oymap="$studio/build/oymap"

[ -d "$root" ] || cp -al "$repo/assets_dev" "$root"
"$oymap" fmt "$project" --check
"$oymap" build "$project" --assets "$repo/assets_dev"
"$oymap" install "$project" --root "$root"
mkdir -p "$run"
(cd "$run" && "$repo/build/game/openyamm" --asset-root "$root" --world mm6 \
    --headless-run-scenario "$project/playtest.yml" --scenario-no-color | grep -E "^(PLAY|FAIL|ASSERT fail|Scenario)" )

# The same build played from a mount folder over assets_dev (the game's --extra-mount): nothing is copied into a root.
"$oymap" install "$project" --mount "$run/mount" --assets "$repo/assets_dev" > /dev/null
(cd "$run" && "$repo/build/game/openyamm" --asset-root "$repo/assets_dev" --extra-mount "$run/mount" --world mm6 \
    --headless-run-scenario "$project/playtest.yml" --scenario-no-color | grep -E "^(FAIL|ASSERT fail|Scenario)" )

# The installed map, read back as the game reads it: no wiring errors, and it opens up in the designed order
# (hall, the two click doors, the lever's gate, then the strong room with its key).
"$oymap" audit studio01.blv --world mm6 --assets "$root" --reach > "$run/audit.txt" || { cat "$run/audit.txt"; exit 1; }
grep -q "2 of 6 sectors with the doors as they start, 6 with every door out of the way" "$run/audit.txt"
"$oymap" solve studio01.blv --world mm6 --assets "$root" > "$run/solve.txt"
grep -q "step 3: 1 sectors (6 of 6), needs \[item 2177\]" "$run/solve.txt"
grep -q "never reached: 0 sectors" "$run/solve.txt"
echo "audit and solve of the installed slice: as designed"

if [ "${1:-}" = "--shots" ]; then
    shots="$repo/output/studio_slice_shots"
    mkdir -p "$shots"
    sed "s|@OUTPUT@|$shots|" "$project/tour.yml" > "$shots/tour.yml"
    "$repo/tools/run_game.sh" --isolated studioslice --world mm6 --map studio01.blv --assets "$root" \
        --warmup 5 --seconds 40 --set "debug.screenshot_tour_path=$shots/tour.yml" | tail -1
    ls "$shots"
fi
