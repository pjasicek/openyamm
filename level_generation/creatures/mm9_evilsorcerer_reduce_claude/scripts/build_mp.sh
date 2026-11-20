#!/usr/bin/env bash
# Evil Sorcerer copy of the Dwarf's (build_lods_mp.py: soles, crown top, corpse contact, tips; snapped). Fix-pass build (chart-guarded mpqem step) -> runtime candidate: swap_mp.py (index buffers into the installed LOD0; every
# vertex attribute exact, the axe primitive unchanged) -> build_lods.py (tools/build_actor_lods.py ratios, 4 influences,
# spike/horn tips/soles/skirt hand-over protected, points snapped to the imported vertices) -> shrink_shadow_lods ->
# carry_variants -> check_winding -> same_clips (clips, skin, nodes, images, materials, variants = installed bytes).
# Usage (any folder): build_mp.sh <mp npz under work/, e.g. mp_a_r40> [out glb, default export_mp/mm9_evilsorcerer.glb]
set -euo pipefail
export MP_NODE=Sorcerer MP_KEPT_PRIMS= CORPSE_CLIPS=${CORPSE_CLIPS:-Dead} LIE=${LIE:-0.004}   # Death+Death2+Dead at 1 cm: 690 points stopped LOD3 at 1,647; Dead at 1 cm: 11 stretched LOD2/3 faces
tag=$1; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
OUT=${2:-export_mp/mm9_evilsorcerer.glb}; o=work/b_$tag; mkdir -p "$(dirname $OUT)"
$G scripts/swap_mp.py before/mm9_evilsorcerer.glb work/$tag.npz ${o}_lod0.glb 2>&1 | grep -v Unexpected
$BL --disable-autoexec --python scripts/build_lods_mp.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" Sorcerer 2>&1 </dev/null | grep -E "PROTECT|SNAP|LOD triangles|Error|Traceback"
$G ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py ${o}_lods.glb $OUT Sorcerer 2>&1 | grep -v Unexpected | tail -1 | cut -c1-160
$G scripts/carry_variants.py $OUT 2>&1 | grep -v Unexpected
$G ../mm9_evilsorcerer_claude/scripts/fix_winding.py $OUT ${o}_wound.glb 2>&1 | grep -v Unexpected | tail -1 | cut -c1-160; mv ${o}_wound.glb $OUT   # as the creature's rebuild.sh
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
$G scripts/same_parts.py before/mm9_evilsorcerer.glb $OUT 2>&1 | grep -v Unexpected | tail -3
ls -la $OUT
