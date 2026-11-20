#!/usr/bin/env bash
# Pose-aware step -> BOTH runtime candidates of the girl family from one cut (mpqem.py ran on the elf GLB, the superset):
#   elf:   the cut as is (body PeasantGirl_G1E, head PeasantGirlHead incl. the ears, kept whole);
#   human: the same body index buffer under PeasantGirl_G2 and the head minus the ear faces (the human head's vertices are the elf
#          head's first 3613 vertices, same order: checked in derive_human.py).
# Each: swap_mp (index buffers into the installed LOD0, every vertex attribute exact) -> build_lods.py (tools/build_actor_lods.py,
# 4 influences, soles / crown / corpse contact protected and snapped) -> shrink_shadow_lods (mm9_skeletonwarrior_claude, as the
# creature's build_runtime.sh) -> carry_variants -> the creature's fix_winding -> check_winding.
# Usage (any folder): build_mp.sh <mp npz under work/, e.g. mp_a_r50> <out tag, e.g. a50>  -> export/cand_<tag>/mm9_peasantgirl{,1e}.glb
set -euo pipefail
tag=$1; ot=$2; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
H=../mm9_peasantgirl_claude/scripts; mkdir -p export/cand_$ot
$G scripts/derive_human.py work/$tag.npz work/${tag}_h.npz 2>&1 | grep -v Unexpected
for v in e h; do
  if [[ $v == e ]]; then src=before/mm9_peasantgirl1e.glb; mp=work/$tag.npz; OUT=export/cand_$ot/mm9_peasantgirl1e.glb
  else src=before/mm9_peasantgirl.glb; mp=work/${tag}_h.npz; OUT=export/cand_$ot/mm9_peasantgirl.glb; fi
  o=work/b_${ot}_$v
  $G scripts/swap_mp.py $src $mp ${o}_lod0.glb 2>&1 | grep -v Unexpected
  $BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" 2>&1 </dev/null | grep -E "LOD triangles|PROTECTED|Error"
  $G ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py ${o}_lods.glb ${o}_sf.glb PeasantGirl 2>&1 | grep -v Unexpected | tail -1 | cut -c1-200
  $G scripts/carry_variants.py ${o}_sf.glb 2>&1 | grep -v Unexpected
  $G $H/fix_winding.py ${o}_sf.glb $OUT 2>&1 | grep -v Unexpected | tail -1
  if [[ -f ${o}_lods.geometry.glb ]]; then rm ${o}_lods.geometry.glb; fi
  $G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
  ls -la $OUT
done
