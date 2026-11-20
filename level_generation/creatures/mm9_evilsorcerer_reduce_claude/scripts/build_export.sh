#!/usr/bin/env bash
# Picked ladder step -> runtime candidate, the Sorcerer's own LOD chain (../mm9_evilsorcerer_claude/scripts/rebuild.sh after
# the floor pass): export_cand (floor = source's lowest point) -> swap_lod0 into the installed GLB (materials, variants,
# tier images, region masks, clips, sockets stay byte for byte) -> fix_normals (installed normals on source vertices, the
# build's rule on new ones) -> build_lods.py (tools/build_actor_lods.py, 4 influences, soles/crown/corpse floor locked) -> shrink_shadow_lods (skeleton warrior's, as
# rebuild.sh) -> carry_variants -> fix_winding (the creature's) -> winding check -> clip bytes check.
# Usage (project folder): build_export.sh <ladder label> <tag, e.g. r70> [final]
#   -> work/<label><tag>_lod0.glb; with "final" -> export/mm9_evilsorcerer.glb
set -euo pipefail
label=$1; tag=$2; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"; G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
n=mm9_evilsorcerer; w=work/${label}${tag}
REA_BLEND=ladder_$label.blend REA_CAND=Cand_${tag#r} REA_NODE=Sorcerer REA_OUT=${label}${tag}_cand.glb $BL -P scripts/export_cand.py 2>&1 | grep -E "FLOOR|EXPORTED|Error"
$G scripts/swap_lod0.py before/$n.glb ${w}_cand.glb ${w}_swap.glb Sorcerer 2>&1 | grep -v Warn
$G scripts/fix_normals.py before/$n.glb ${w}_swap.glb ${w}_lod0.glb Sorcerer 2>&1 | grep -v Warn
[ "${3:-}" == final ] || exit 0
$BL --disable-autoexec -P scripts/build_lods.py -- "$PWD/${w}_lod0.glb" "$PWD/${w}_lods.glb" 2>&1 </dev/null | grep -E "PROTECTED|LOD triangles|Error"
$G ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py ${w}_lods.glb ${w}_sf.glb Sorcerer 2>&1 | grep -v Warn | tail -1 | cut -c1-160
$G scripts/carry_variants.py ${w}_sf.glb 2>&1 | grep -v Warn
$G ../mm9_evilsorcerer_claude/scripts/fix_winding.py ${w}_sf.glb export/$n.glb 2>&1 | grep -v Warn | tail -1 | cut -c1-160
if [[ -f ${w}_lods.geometry.glb ]]; then rm ${w}_lods.geometry.glb; fi
$G "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/$n.glb 2>&1 | grep -v Warn | tail -1
$G scripts/same_parts.py before/$n.glb export/$n.glb
ls -la export/$n.glb
