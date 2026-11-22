#!/usr/bin/env bash
# Build the great-tree crown (species/<id>.json) with its own shared textures (shared/, from scripts/make_shared.py):
# envelope silhouette -> profile -> crown (limbs, clumps, occlusion, LOD subsets) -> LOD2 clump cards -> impostor ->
# far maps to 512² -> export -> link + validate [--install via tools/install_model.py --world xeen] -> review sheets.
# Adapted from ../mm8_3d/trees_broadleaf/build.sh. Blender goes through the lane S wrapper (one Blender at a time).
# Usage: build.sh <id> [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export PATH="/home/pjasicek/github/OpenYAMM/level_generation/creatures/xeen_tiers_claude/bin:$PATH"
blender="/home/pjasicek/github/OpenYAMM/level_generation/creatures/xeen_tiers_claude/bin/blender"
id="$1"; shift
cd "$here/scripts"
[[ -f ../shared/atlas.json ]] || python3 make_shared.py
python3 make_envelope.py "$id"
python3 prepare.py "$id"
"$blender" --background --python build_tree.py -- "$id" 2>&1 | grep -E "TINT|SKELETON|BARK|CLUMPS|CARDS|SHELL|VIEW|OCCLUSION|LEAVES|^LOD|Error|Traceback"
"$blender" --background --python clump_cards.py -- "$id" 2>&1 | grep -E "CLUMP|Error|Traceback"
python3 make_clump_atlas.py "$id"
"$blender" --background --python clump_lod2.py -- "$id" 2>&1 | grep -E "LOD2|Error|Traceback"
"$blender" --background --python bake_impostor.py -- "$id" 2>&1 | grep -E "IMPOSTOR|Error|Traceback"
python3 finish_impostor.py "$id"
python3 shrink_far_maps.py "$id"
"$blender" --background --python export_tree.py -- "$id" 2>&1 | grep -E "EXPORTED|Error|Traceback"
python3 post_process.py "$id" "$@" | tee "../work/$id/validation.txt"
python3 review.py "$id"
python3 lod_check.py "$id"
python3 stack_sheet.py "$id"
