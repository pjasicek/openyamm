#!/usr/bin/env bash
# Picked step (work/mp_<tag>.npz) -> runtime candidate. Usage (any folder): build_cand.sh <tag, e.g. r45> [out.glb]
#  swap_inst.py (installed GLB, LOD0 index buffers swapped, every vertex attribute the installed bytes, old LODs dropped)
#  -> tools/build_actor_lods.py (as the model was built: default ratios, 4 influences) -> shrink_shadow_lods (as the
#  Nosferatu's rebuild.sh) -> carry_variants -> head_splice (installed head primitive on LOD1-3) -> the Nosferatu's own
#  fix_winding.py (coarse LODs only) -> check_winding, same_clips.
set -euo pipefail
tag=$1; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
o=work/c_${tag}; OUT=${2:-export/mm9_nosferatu_${tag}.glb}
$G scripts/swap_inst.py before/mm9_nosferatu.glb work/mp_${tag}.npz ${o}_lod0.glb 2>&1 | grep -v Unexpected
$BL --disable-autoexec --python "$R/tools/build_actor_lods.py" -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" --mesh-node Nosferatu --max-influences 4 2>&1 </dev/null | grep -E "LOD triangles|Error"
$G ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py ${o}_lods.glb ${o}_sf.glb Nosferatu 2>&1 | grep -v Unexpected | tail -1 | cut -c1-200
$G scripts/carry_variants.py ${o}_sf.glb 2>&1 | grep -v Unexpected
$G scripts/head_splice.py before/mm9_nosferatu.glb ${o}_sf.glb ${o}_hs.glb 2>&1 | grep -v Unexpected
$G ../mm9_nosferatu_claude/scripts/fix_winding.py ${o}_hs.glb $OUT 2>&1 | grep -v Unexpected | tail -1
if [[ -f ${o}_lods.geometry.glb ]]; then rm ${o}_lods.geometry.glb; fi
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
$G scripts/same_clips.py before/mm9_nosferatu.glb $OUT 2>&1 | grep -v Unexpected | tail -2
$G scripts/glbinfo.py $OUT 2>&1 | grep -v Unexpected | head -4
ls -la $OUT
