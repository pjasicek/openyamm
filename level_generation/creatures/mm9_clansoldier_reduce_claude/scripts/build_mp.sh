#!/usr/bin/env bash
# Fix-pass build (chart-guarded mpqem step) -> runtime candidate: swap_mp.py (index buffers into the installed LOD0; every
# vertex attribute exact, the weapons primitive unchanged) -> build_lods.py (tools/build_actor_lods.py ratios, 4 influences,
# soles, top and corpse contact protected, points snapped to the imported vertices) -> shrink_shadow_lods ->
# carry_variants -> check_winding -> same_clips (clips, skin, nodes, images, materials, variants = installed bytes).
# Usage (any folder): build_mp.sh <mp npz under work/, e.g. mp_a_r40> [out glb, default export_mp/mm9_clansoldier.glb]
set -euo pipefail
tag=$1; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
OUT=${2:-export_mp/mm9_clansoldier.glb}; o=work/b_$tag; mkdir -p "$(dirname $OUT)"
$G scripts/swap_mp.py before/mm9_clansoldier.glb work/$tag.npz ${o}_lod0.glb 2>&1 | grep -v Unexpected
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" 2>&1 </dev/null | grep -E "PROTECT|SNAP|LOD triangles|Error|Traceback"
$G scripts/shrink_shadow_lods.py ${o}_lods.glb $OUT ClanSoldier 2>&1 | grep -v Unexpected | tail -1 | cut -c1-160
$G scripts/carry_variants.py $OUT 2>&1 | grep -v Unexpected
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
$G scripts/same_clips.py before/mm9_clansoldier.glb $OUT 2>&1 | grep -v Unexpected | tail -1
ls -la $OUT
