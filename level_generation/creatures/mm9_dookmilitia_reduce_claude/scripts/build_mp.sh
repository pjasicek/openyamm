#!/usr/bin/env bash
# Pose-aware step -> runtime candidate (fix pass; Half-Orc copy of mm9_lizardorc_reduce_claude/scripts/build_mp.sh): swap_mp
# (index buffers into the installed LOD0, every vertex attribute exact; the sword primitive keeps its accessors) -> floor_points
# -> build_lods.py (tools/build_actor_lods.py, 4 influences, default ratios, soles/corpse/top protected with the snap fix) ->
# shrink_shadow_lods -> carry_variants -> the creature's fix_winding -> check_winding -> same_clips -> the shared UV audit.
# Usage (project folder): build_mp.sh <mp npz under work/, e.g. mp_M1_r55> <out glb>
set -euo pipefail
tag=$1; OUT=$2; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
o=work/b_$tag
$G scripts/swap_mp.py before/mm9_dookmilitia.glb work/$tag.npz ${o}_lod0.glb 2>&1 | grep -v Unexpected
$G scripts/floor_points.py ${o}_lod0.glb 2>&1 | grep FLOORPOINTS
$BL --disable-autoexec -P scripts/build_lods.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" 2>&1 </dev/null | grep -E "LOD triangles|PROTECTED|Error|Traceback"
$G scripts/shrink_shadow_lods.py ${o}_lods.glb ${o}_sf.glb DookMilitia 2>&1 | grep -v Unexpected | tail -1 | cut -c1-200
$G scripts/carry_variants.py ${o}_sf.glb 2>&1 | grep -v Unexpected
$G scripts/fix_winding.py ${o}_sf.glb $OUT 2>&1 | grep -v Unexpected | tail -1
if [[ -f ${o}_lods.geometry.glb ]]; then rm ${o}_lods.geometry.glb; fi
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
$G scripts/same_clips.py before/mm9_dookmilitia.glb $OUT 2>&1 | grep -v Unexpected | tail -1
$G ../claude_shared/reduction_uv_audit.py $OUT before/mm9_dookmilitia.glb --json ${OUT%.glb}_uv_audit.json 2>&1 | grep -v Unexpected | grep LOD0
ls -la $OUT
