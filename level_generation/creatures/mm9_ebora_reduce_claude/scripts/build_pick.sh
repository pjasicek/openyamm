#!/usr/bin/env bash
# Picked ladder step -> runtime candidate. Usage: build_pick.sh <ladder label> <tag, e.g. r80> [final]
# work/<label><tag>_lod0.glb (LOD0 swapped, installed normals on source vertices); with "final": LODs (build_actor_lods, Ebora's
# ratios and 4 influences), shadow shrink, variants carried, Ebora's LOD winding fix -> export/mm9_ebora.glb
# (build_actor_lods leaves work/<label><tag>_lods.geometry.glb behind: a scratch file, safe to delete by its literal name)
set -euo pipefail
label=$1; tag=$2; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"; G=../claude_shared/gltf_venv/bin/python
REA_BLEND=ladder_$label.blend REA_CAND=Cand_${tag#r} REA_NODE=Ebora REA_OUT=${label}${tag}_cand.glb scripts/bl.sh scripts/export_cand.py 2>&1 | grep -E "EXPORTED|Error"
$G -W ignore scripts/swap_lod0.py before/mm9_ebora.glb work/${label}${tag}_cand.glb work/${label}${tag}_swap.glb Ebora 2>&1 | grep -v Warn
$G -W ignore scripts/fix_normals.py before/mm9_ebora.glb work/${label}${tag}_swap.glb work/${label}${tag}_lod0.glb Ebora 2>&1 | grep -v Warn
[ "${3:-}" == final ] || exit 0
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$R/tools/build_actor_lods.py" -- "$PWD/work/${label}${tag}_lod0.glb" "$PWD/work/${label}${tag}_lods.glb" --mesh-node Ebora --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
$G -W ignore ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py work/${label}${tag}_lods.glb work/${label}${tag}_sf.glb Ebora 2>&1 | grep -v Warn | tail -1
$G -W ignore scripts/carry_variants.py work/${label}${tag}_sf.glb 2>&1 | grep -v Warn
$G -W ignore ../mm9_ebora_claude/scripts/fix_winding.py work/${label}${tag}_sf.glb export/mm9_ebora.glb 2>&1 | grep -v Warn | tail -1
$G -W ignore scripts/compact.py export/mm9_ebora.glb 2>&1 | grep -v Warn
$G -W ignore "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_ebora.glb 2>&1 | grep -v Warn | tail -1
$G -W ignore ../claude_shared/bone_length_audit.py export/mm9_ebora.glb 2>&1 | grep -v Warn | tail -1
ls -la export/mm9_ebora.glb
