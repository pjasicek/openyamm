#!/usr/bin/env bash
# One cut -> four runtime candidates: swap_df.py (DF1's reduced index buffers onto each design's installed LOD0, every vertex
# attribute exact; head rows per design) -> build_lods.py (tools/build_actor_lods.py defaults 0.5/0.18/0.06, 4 influences,
# soles/crown/corpse contact protected and snapped) -> the creature's shrink_shadow_lods.py (ears leave shadow LOD2/3) ->
# carry_variants.py -> check_winding. Clips, materials, variants, images: the installed design's.
# Usage (project folder): scripts/build_df.sh <mp npz tag, e.g. mp_f_r55> [designs, default 1 2 3 4]
set -euo pipefail
tag=$1; shift; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
for n in ${@:-1 2 3 4}; do
  o=work/b_${tag}_d$n; OUT=${OUTDIR:-export}/mm9_peasantdf$n.glb; mkdir -p ${OUTDIR:-export}
  $G scripts/swap_df.py $n work/$tag.npz ${o}_lod0.glb 2>&1 | grep -v Unexpected
  $BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" 2>&1 </dev/null | grep -E "LOD triangles|PROTECTED|Error"
  $G ../mm9_peasantdf_claude/scripts/shrink_shadow_lods.py ${o}_lods.glb ${o}_sf.glb PeasantDF 2>&1 | grep -v Unexpected | tail -1 | cut -c1-200
  $G scripts/carry_variants.py ${o}_sf.glb 2>&1 | grep -v Unexpected
  cp ${o}_sf.glb $OUT
  if [[ -f ${o}_lods.geometry.glb ]]; then rm ${o}_lods.geometry.glb; fi
  python3 "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | tail -1
done
ls -la ${OUTDIR:-export}/
