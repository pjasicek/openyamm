#!/usr/bin/env bash
# S2 acceptance: the two rewire overlays (examples/goblinwatch_vault, examples/new_sorpigal_wells) play the same as
# the shipped maps. Builds both, installs them into a scratch asset root (a hard-link copy of assets_dev under
# output/), then (1) requires that every replaced handler tests and does the same things as the original, by running
# both in the sandbox, and (2) plays a scripted scenario on the shipped map, on the overlaid one in the scratch
# root, and on assets_dev with the overlay in a mount folder (the game's --extra-mount), and requires the same log
# from all three.
set -euo pipefail
studio="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd "$studio/.." && pwd)"
oymap="$studio/build/oymap"
root="$repo/output/studio_rewire_root"
run="$repo/output/studio_rewire_run"
[ -d "$root" ] || cp -al "$repo/assets_dev" "$root"
mkdir -p "$run"

for entry in "goblinwatch_vault 6d01.blv" "new_sorpigal_wells oute3.odm"; do
    set -- $entry
    project="$studio/examples/$1"
    "$oymap" build "$project" --assets "$repo/assets_dev" > /dev/null
    "$oymap" install "$project" --root "$root" > /dev/null
    "$oymap" install "$project" --mount "$run/mount" --assets "$repo/assets_dev" > /dev/null
    "$oymap" flow "$2" --world mm6 --assets "$repo/assets_dev" > "$run/$1.base.json"
    "$oymap" flow "$2" --world mm6 --assets "$root" > "$run/$1.overlay.json"
    python3 "$studio/tests/compare_flows.py" "$run/$1.base.json" "$run/$1.overlay.json" "$project" "$1"
    for side in base overlay mount; do
        assets="$repo/assets_dev"; [ "$side" = overlay ] && assets="$root"
        extra=(); [ "$side" = mount ] && extra=(--extra-mount "$run/mount")
        (cd "$run" && "$repo/build/game/openyamm" --asset-root "$assets" "${extra[@]}" --world mm6 \
            --headless-run-scenario "$project/playtest.yml" --scenario-no-color > "$run/$1.$side.full.log" 2>&1) || true
        grep -E "^(PLAY|FAIL|ASSERT|Scenario)" "$run/$1.$side.full.log" > "$run/$1.$side.log" || true
        grep -q "^Scenario passed" "$run/$1.$side.log"
    done
    grep -q "studio_rewire_run/mount/worlds/mm6/events" "$run/$1.mount.full.log"
    diff "$run/$1.base.log" "$run/$1.overlay.log" > /dev/null && diff "$run/$1.base.log" "$run/$1.mount.log" > /dev/null \
        && echo "$1: the scenario's log is the same on the shipped map, the overlaid root and the mount ($(grep -c '^PLAY' "$run/$1.base.log") lines)"
done

# Control: the same log must not come from an overlay that was never read. A second mount whose overlay empties
# Goblinwatch's key B (event 20) has to change the scenario's log.
control="$run/control_mount/worlds/mm6/events/maps"
mkdir -p "$control"
printf 'evt.map[20] = function() end\n' > "$control/6d01_zzcontrol.lua"
(cd "$run" && "$repo/build/game/openyamm" --asset-root "$repo/assets_dev" --extra-mount "$run/control_mount" --world mm6 \
    --headless-run-scenario "$studio/examples/goblinwatch_vault/playtest.yml" --scenario-no-color 2>&1 \
    | grep -E "^(PLAY|FAIL|ASSERT|Scenario)" > "$run/control.log") || true
if diff "$run/goblinwatch_vault.base.log" "$run/control.log" > /dev/null; then
    echo "control: an overlay that empties key B did not change the log: mounted overlays are not being read"
    exit 1
fi
echo "control: an overlay in a mount that empties key B changes the log, as it must"
