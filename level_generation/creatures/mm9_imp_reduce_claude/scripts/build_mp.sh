#!/usr/bin/env bash
# Pose-aware step -> runtime candidate: swap_mp (index buffers into the installed LOD0, every vertex attribute exact; the head
# primitive keeps its accessors) -> LODs as the Gezzampt was built (tools/build_actor_lods.py default ratios, 4 influences,
# here with soles, crown and corpse contact protected: build_lods.py) -> the Troglodyte's shrink_shadow_lods -> carry_variants
# -> its fix_winding -> check_winding. Clips, materials, variants, region masks, tier C images stay the installed bytes
# (region_variants, tier_c, floor_fix and tone were applied to the installed file already; nothing here re-runs them).
# Imp copy of the Gezzampt's (shrink_shadow_lods and fix_winding read from ../mm9_imp_claude/scripts, as the model was built).
# Usage (any folder): build_mp.sh <mp npz under work/, e.g. mp_a_r55> [out glb, default export/mm9_imp_<tag>.glb]
set -euo pipefail
tag=$1; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
H=../mm9_imp_claude/scripts; o=work/b_$tag; OUT=${2:-export/mm9_imp_$tag.glb}
$G scripts/swap_mp.py before/mm9_imp.glb work/$tag.npz ${o}_lod0.glb 2>&1 | grep -v Unexpected
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" 2>&1 </dev/null | grep -E "LOD triangles|PROTECTED|EAR|TIP|CLAW|HORN|TAIL|Error|Traceback"
$G $H/shrink_shadow_lods.py ${o}_lods.glb ${o}_sf.glb Imp 2>&1 | grep -v Unexpected | tail -1 | cut -c1-200
$G scripts/carry_variants.py ${o}_sf.glb 2>&1 | grep -v Unexpected
$G $H/fix_winding.py ${o}_sf.glb $OUT 2>&1 | grep -v Unexpected | tail -1
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
$G scripts/same_clips.py before/mm9_imp.glb $OUT 2>&1 | grep -v Unexpected | tail -1
ls -la $OUT
