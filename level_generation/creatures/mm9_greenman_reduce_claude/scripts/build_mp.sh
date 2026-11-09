#!/usr/bin/env bash
# Pose-aware step -> runtime candidate: swap_mp (index buffers into the installed LOD0, every vertex attribute exact) ->
# the Highwayman's LOD chain (tools/build_actor_lods.py, 4 influences -> its shrink_shadow_lods -> carry_variants -> its
# fix_winding) -> check_winding. Clips (floor-fixed), materials, variants and images stay the installed ones.
# Green Man (as Sigmund): the creature's own chain after its LODs (build_runtime_sig.sh: shrink_shadow_lods, drop_lod_slivers, read in place;
# materials/extras, floor-fixed clips and the mirror are already in the installed LOD0, which is mirrored before the LODs here).
# Usage (any folder): build_mp.sh <mp npz under work/, e.g. mp_m1_r50> [out glb, default export/mm9_thrall_<tag>.glb]
set -euo pipefail
tag=$1; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
H=../mm9_greenman_claude/scripts; o=work/b_$tag; OUT=${2:-export/mm9_greenman_$tag.glb}
$G scripts/swap_mp.py before/mm9_greenman.glb work/$tag.npz ${o}_lod0.glb 2>&1 | grep -v Unexpected
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" 2>&1 </dev/null | grep -E "LOD triangles|PROTECTED|Error"
$G $H/shrink_shadow_lods.py ${o}_lods.glb ${o}_sf.glb GreenMan 2>&1 | grep -v Unexpected | tail -1 | cut -c1-200
$G $H/drop_lod_slivers.py ${o}_sf.glb ${o}_ds.glb 2>&1 | grep -v Unexpected | tail -1
# Green Man: thin closed leaf shells of ~0 volume in the rebuilt LODs/shadows turned outward (the creature's fix_winding.py)
$G $H/fix_winding.py ${o}_ds.glb $OUT 2>&1 | grep -v Unexpected | tail -1
if [[ -f ${o}_lods.geometry.glb ]]; then rm ${o}_lods.geometry.glb; fi
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
ls -la $OUT
