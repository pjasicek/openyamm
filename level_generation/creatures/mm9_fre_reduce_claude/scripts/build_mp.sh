#!/usr/bin/env bash
# Pose-aware step -> runtime candidate (from mm9_peasantf4_reduce_claude/scripts/build_mp.sh): swap_mp (index buffers into the installed
# LOD0, every vertex attribute exact) -> Fre's LOD chain (tools/build_actor_lods.py through build_lods.py with snapped protected points,
# 4 influences -> shrink_shadow_lods -> Fre's fix_winding) -> check_winding. Clips (floor-fixed, mirrored), materials (FreHair
# doubleSided, specular extras), images stay the installed ones. Fre has one skin and no KHR_materials_variants (no carry_variants).
# Usage (any folder): build_mp.sh <mp npz under work/, e.g. mp_a_r50> [out glb, default export/mm9_fre_<tag>.glb]
set -euo pipefail
tag=$1; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
o=work/b_$tag; OUT=${2:-export/mm9_fre_$tag.glb}
$G scripts/swap_mp.py before/mm9_fre.glb work/$tag.npz ${o}_lod0.glb 2>&1 | grep -v Unexpected
$G scripts/single_hair.py ${o}_lod0.glb ${o}_lod0s.glb 2>&1 | grep -v Unexpected
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/${o}_lod0s.glb" "$PWD/${o}_lods.glb" 2>&1 </dev/null | grep -E "LOD triangles|PROTECTED|Error"
$G ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py ${o}_lods.glb ${o}_sf.glb Fre 2>&1 | grep -v Unexpected | tail -1 | cut -c1-200
(cd ../mm9_fre_claude && ../claude_shared/gltf_venv/bin/python -W ignore scripts/double_hair_fre.py "$OLDPWD/${o}_sf.glb" "$OLDPWD/${o}_sfd.glb" 2>&1 | grep -v Unexpected)
$G ../mm9_fre_claude/scripts/fix_winding.py ${o}_sfd.glb $OUT 2>&1 | grep -v Unexpected | tail -1
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
ls -la $OUT
