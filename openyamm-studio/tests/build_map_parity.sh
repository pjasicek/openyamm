#!/usr/bin/env bash
# `oymap build-map` against maps the editor's --headless-build-map built: the same bytes. Copies each source package
# into an empty folder (so the map is built from its sources, not patched) and compares the .odm with the one kept in
# the repository. Needs the local level_generation folders and stage roots; skips what is not there.
set -uo pipefail
studio="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd "$studio/.." && pwd)"
failed=0
checked=0

# The build writes map_stats and map_navigation rows into the asset root's editor folder (the root itself when it is
# named assets_editor_dev, else its sibling of that name), as the editor does. A parity run must not touch a real
# root's tables: it builds against a hard-link copy named assets_dev under output/studio_parity/, so the rows land in
# that copy's sibling.
scratch_root() {  # <asset root> <key>
    copy="$repo/output/studio_parity/$2/assets_dev"
    [ -d "$copy" ] || { mkdir -p "$(dirname "$copy")" && cp -al "$1" "$copy"; }
    echo "$copy"
}

check() {  # <source dir> <stem> <asset root> <expected odm> <key>
    [ -f "$1/$2.map.yml" ] && [ -f "$4" ] && [ -d "$3" ] || { echo "skipped $2 ($1)"; return; }
    work="$(mktemp -d)"
    cp "$1/$2.map.yml" "$1/$2.scene.yml" "$1/$2.geometry.yml" "$1/$2.terrain.yml" "$work/"
    if "$studio/build/oymap" build-map "$work/$2.map.yml" --asset-root "$(scratch_root "$3" "$5")" > "$work/log" 2>&1 \
        && cmp -s "$work/$2.odm" "$4"; then
        echo "identical $2 ($(stat -c %s "$4") bytes)"
    else
        echo "DIFFERENT $2: $(tail -1 "$work/log")"
        failed=$((failed + 1))
    fi
    checked=$((checked + 1))
}

for fixture in "$repo"/level_generation/terrain/mm8/fixtures/land_v1/*/; do
    check "${fixture%/}" out01 "$repo/assets_dev" "${fixture}out01.odm" dev
done
for n in 1 2 3 4; do
    check "$repo/level_generation/projects/hesper_out$n/source" "hes_out$n" \
        "$repo/output/hesper_stage/assets_editor_dev" \
        "$repo/level_generation/projects/hesper_out$n/runtime/worlds/hesper/maps/hes_out$n.odm" hesper
done

echo "build-map parity: $((checked - failed)) of $checked"
[ "$failed" -eq 0 ]
