#!/usr/bin/env bash
# Pose-aware step -> runtime candidate (Krohn): swap_mp (index buffers into the installed LOD0, every vertex attribute exact) ->
# build_lods.py (tools/build_actor_lods.py 0.5/0.18/0.06, 4 influences as the model was built; soles, crown top and corpse floor
# contact protected, snapped) -> Krohn's own shrink_shadow_lods.py (one-texel lining triangles out of the shadows) ->
# Krohn's drop_lod_slivers.py (flat LOD slivers, the glaive blade in the LOD2 shadow) -> Yanmir's fix_winding.py -> check_winding. The clips (floor-fixed,
# walk floor, mirrored at the build), materials (extras), images and nodes stay the installed ones.
# Usage (any folder): build_mp.sh <mp npz under work/, e.g. mp_a_r55> [out glb, default export/mm9_krohn_<tag>.glb]
set -euo pipefail
tag=$1; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
H=../mm9_krohn_claude/scripts; o=work/b_$tag; OUT=${2:-export/mm9_krohn_$tag.glb}
$G scripts/swap_mp.py before/mm9_krohn.glb work/$tag.npz ${o}_lod0.glb 2>&1 | grep -v Unexpected
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" 2>&1 </dev/null | grep -E "LOD triangles|PROTECTED|Error"
python3 $H/shrink_shadow_lods.py ${o}_lods.glb ${o}_sf.glb Krohn 2>&1 | tail -1 | cut -c1-200
python3 $H/drop_lod_slivers.py ${o}_sf.glb ${o}_sl.glb 2>&1 | tail -1 | cut -c1-200
# a decimated LOD bit closed inside out (b70: a 4-triangle tetrahedron of the back flap in LOD3): Yanmir's fix_winding turns it out
$G ../mm9_yanmir_claude/scripts/fix_winding.py ${o}_sl.glb $OUT 2>&1 | grep -v Unexpected | tail -1
if [[ -f ${o}_lods.geometry.glb ]]; then rm ${o}_lods.geometry.glb; fi
python3 "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | tail -1
ls -la $OUT
