#!/usr/bin/env bash
# Leftover MM6 dungeon trees and flowers (see ../README.md): copied outdoor tree pipeline (trees/, species in species/)
# or flower pipeline (flowers/) -> unlinked, card-cut export in work/plants/<id>/ -> batch review.py + sheet.py
# (review/<id>/compare.png) -> finish.py (link LODs, validate) [--install].
# Usage: build_plants.sh <id> [--install]     ids: 6tree09 6tree22 6tree26 6tree30 6flower01 6flower11
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
id="$1"; shift
batch="$(dirname "$here")"
case "$id" in
  6flower*)
    cd "$here/flowers"
    python3 make_atlas.py "$id"
    tris=$("$blender" --background --python build_plant.py -- "$id" 2>&1 | grep -E '^LOD' | awk '{print $4}' | tr '\n' ' ')
    echo "LOD triangles before cutting: $tris"
    python3 post_process.py "$id"
    "$blender" --background --python render_review.py -- "$id" 2>&1 | grep -c RENDERED > /dev/null || true
    python3 sheet.py "$id" $tris
    export_glb="$batch/work/plants/$id/plant_cut.glb"; yaw=0 ;;
  *)
    cd "$here/trees"
    python3 prepare.py "$id" | grep -E "BARK"
    python3 make_leaf_atlas.py "$id"
    "$blender" --background --python build_tree.py -- "$id" 2>&1 | grep -E "BARK|CLUMPS|CARDS|OCCLUSION|LEAVES|MOSS|^LOD|Error|Traceback"
    "$blender" --background --python clump_cards.py -- "$id" 2>&1 | grep -E "CLUMP|Error|Traceback"
    python3 make_clump_atlas.py "$id"
    "$blender" --background --python clump_lod2.py -- "$id" 2>&1 | grep -E "LOD2|Error|Traceback"
    "$blender" --background --python bake_impostor.py -- "$id" 2>&1 | grep -E "IMPOSTOR|Error|Traceback"
    python3 finish_impostor.py "$id"
    python3 shrink_far_maps.py "$id"
    "$blender" --background --python export_tree.py -- "$id" 2>&1 | grep -E "EXPORTED|Error|Traceback"
    python3 post_process.py "$id" | tee "$batch/work/plants/$id/validation.txt"
    python3 ../plant_tint.py "$id"          # COLOR_0 x species albedo_tint: flat albedo = the native sprite mean
    python3 review.py "$id"
    python3 lod_check.py "$id"
    export_glb="$batch/work/plants/$id/tree_tinted.glb"; yaw=0 ;;
esac
cd "$batch"
"$blender" --background --python scripts/albedo.py -- "$export_glb" 2>&1 | grep -E "ALBEDO all" || true
sprite=$(basename "$(ls "$batch/../../../../assets_dev/engine/decorations_x2/${id}"_p*.png | head -1)")
"$blender" --background --python scripts/review.py -- "$id" "$export_glb" "$yaw" 2>&1 | grep -E "REVIEW|Error|Traceback"
python3 scripts/sheet.py "$id" "$sprite"
python3 scripts/finish.py "$id" "$@"
