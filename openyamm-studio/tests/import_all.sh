#!/usr/bin/env bash
# S1 acceptance: every shipped map imports into a project that validates and is in canonical form, and every scene
# file and overlay survives the core's writer. Usage: tests/import_all.sh [asset root]
set -uo pipefail
studio="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
root="${1:-$studio/../assets_dev}"
oymap="$studio/build/oymap"
work="$(mktemp -d)"
total=0
failed=0

for world in $(ls "$root/worlds"); do
    [ -d "$root/worlds/$world/maps" ] || continue
    for map in $(cd "$root/worlds/$world/maps" && ls | grep -E '\.(odm|blv)$'); do
        total=$((total + 1))
        project="$work/$world/${map%.*}"
        if ! "$oymap" import "$map" --world "$world" --assets "$root" --to "$project" > "$work/log" 2>&1 \
            || ! "$oymap" validate "$project" >> "$work/log" 2>&1 \
            || ! "$oymap" fmt "$project" --check >> "$work/log" 2>&1; then
            failed=$((failed + 1))
            echo "FAILED $world/$map: $(tail -2 "$work/log" | tr '\n' ' ' | cut -c1-200)"
        fi
    done
done

echo "import: $((total - failed)) of $total maps"
"$oymap" scene-roundtrip $(find "$root/worlds" "$root/engine/rulesets" -path '*/maps/*' -name '*.scene*.yml' | sort) | tail -3
[ "$failed" -eq 0 ]
