#!/usr/bin/env bash
# Pose-aware step -> runtime candidate (from mm9_highwayman_reduce_claude): swap_mp (index buffers into the installed LOD0,
# every vertex attribute exact) -> the demon's LOD chain (tools/build_actor_lods.py defaults, 4 influences, protected points
# -> its shrink_shadow_lods -> its fix_winding) -> check_winding -> bone audit. Clips (floor-fixed), materials with their
# extras and images stay the installed ones. Usage (project folder): build_mp.sh <mp npz under work/, e.g. mp_h_r68> [out glb]
set -euo pipefail
tag=$1; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
D=../mm9_stage1demon_claude/scripts; o=work/b_$tag; OUT=${2:-export/mm9_lesserdemon_$tag.glb}
$G scripts/swap_mp.py before/mm9_lesserdemon.glb work/$tag.npz ${o}_lod0.glb
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" 2>&1 </dev/null | grep -E "LOD triangles|PROTECTED|Error"
$G $D/shrink_shadow_lods.py ${o}_lods.glb ${o}_sf.glb LesserDemon 2>&1 | tail -1 | cut -c1-200
$G $D/fix_winding.py ${o}_sf.glb $OUT 2>&1 | tail -1 | cut -c1-200
if [[ -f ${o}_lods.geometry.glb ]]; then rm ${o}_lods.geometry.glb; fi
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | tail -1
$G ../claude_shared/bone_length_audit.py $OUT 2>&1 | tail -1
ls -la $OUT
