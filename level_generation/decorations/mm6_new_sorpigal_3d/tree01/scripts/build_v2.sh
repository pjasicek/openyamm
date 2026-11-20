#!/usr/bin/env bash
# v2 rebuild of mm6_deco_tree01.glb: atlas -> tree (clumps, occlusion COLOR_0, LOD subsets) -> impostor -> export ->
# link + validate (--install copies over the runtime GLB, keeping v1 as work/mm6_deco_tree01_v1.glb) -> review sheets.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
blender=/snap/bin/blender
cd "$here"
python3 scripts/prepare_bark_v2.py
python3 scripts/make_leaf_atlas_v2.py
"$blender" --background --python scripts/build_tree_v2.py 2>&1 | grep -E "BARK|CLUMPS|CARDS|OCCLUSION|LEAVES|^LOD|Error|Traceback"
"$blender" --background --python scripts/clump_cards_v2.py 2>&1 | grep -E "CLUMP|Error|Traceback"
python3 scripts/make_clump_atlas_v2.py
"$blender" --background --python scripts/clump_lod2_v2.py 2>&1 | grep -E "LOD2|Error|Traceback"
"$blender" --background --python scripts/bake_impostor_v2.py 2>&1 | grep -E "IMPOSTOR|Error|Traceback"
python3 scripts/finish_impostor_v2.py
"$blender" --background --python scripts/export_tree_v2.py 2>&1 | grep -E "EXPORTED|Error|Traceback"
python3 scripts/post_process_v2.py "$@" | tee work_v2/validation.txt
python3 scripts/review_v2.py
python3 scripts/lod_check_v2.py
