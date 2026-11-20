#!/usr/bin/env bash
# Lining candidate: line.py (LOD0 rows appended, old LODs dropped) -> the reduction's LOD chain (build_lods.py: protected soles,
# crown and corpse contact, snapped) -> PeasantDM2's shrink_shadow_lods.py (drops the one-texel lining/cap triangles from every
# shadow mesh) -> carry_variants -> the creature's fix_winding.py -> check_winding.
# Usage (any folder): scripts/build.sh <ops json> <tag>   -> export/mm9_pm1d_<tag>.glb, work/line_<tag>.json
set -euo pipefail
ops=$(realpath $1); tag=$2; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
H=../mm9_peasantm1d_claude; o=work/b_$tag; OUT=export/mm9_pm1d_$tag.glb
$G scripts/line.py before/mm9_pm1d.glb ${o}_lod0.glb $ops work/line_$tag.json 2>&1 | grep -v Unexpected | cut -c1-260
cp ${o}_lod0_lining.npz export/mm9_pm1d_${tag}_lining.npz
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/${o}_lod0.glb" "$PWD/${o}_lods.glb" 2>&1 </dev/null | grep -E "LOD triangles|PROTECTED|Error" || true
$G scripts/shrink_shadow_lods_dm2.py ${o}_lods.glb ${o}_sf.glb PM1d 2>&1 | grep -v Unexpected | tail -1 | cut -c1-300
$G scripts/carry_variants.py ${o}_sf.glb 2>&1 | grep -v Unexpected
$G $H/scripts/fix_winding.py ${o}_sf.glb $OUT 2>&1 | grep -v Unexpected | tail -1
if [[ -f ${o}_lods.geometry.glb ]]; then rm ${o}_lods.geometry.glb; fi
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $OUT 2>&1 | grep -v Unexpected | tail -1
sha256sum $OUT
