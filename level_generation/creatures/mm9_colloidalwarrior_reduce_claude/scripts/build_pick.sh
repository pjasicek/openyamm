#!/usr/bin/env bash
# Picked ladder step -> runtime candidate. Usage: build_pick.sh <ladder label> <tag, e.g. r78> [final]
# work/<label><tag>_lod0.glb: LOD0 swapped into the installed file (materials, variants, region masks, floor-fixed clips
# byte for byte), installed normals on every source vertex (copy_kept_normals.py: the kept face renders as installed),
# Blender's smooth normals on new vertices (the colloidal's own export_cw.py rule). With "final", the colloidal's own
# chain after the clips (../mm9_colloidalwarrior_claude/scripts/rebuild.sh): build_actor_lods (default ratios,
# 4 influences) -> its shrink_shadow_lods -> carry_variants -> its fix_winding -> compact -> export/mm9_colloidalwarrior.glb
# (build_actor_lods leaves work/<label><tag>_lods.geometry.glb behind: a scratch file, delete by its literal name)
set -euo pipefail
label=$1; tag=$2; cd "$(dirname "$0")/.."; R="$(cd ../../.. && pwd)"; G=../claude_shared/gltf_venv/bin/python; CW=../mm9_colloidalwarrior_claude/scripts
REA_BLEND=ladder_$label.blend REA_CAND=Cand_${tag#r} REA_NODE=Colloidal REA_OUT=${label}${tag}_cand.glb scripts/bl.sh scripts/export_cand.py 2>&1 | grep -E "EXPORTED|Error"
$G -W ignore scripts/swap_lod0.py before/mm9_colloidalwarrior.glb work/${label}${tag}_cand.glb work/${label}${tag}_swap.glb Colloidal 2>&1 | grep -v Warn
$G -W ignore scripts/copy_kept_normals.py before/mm9_colloidalwarrior.glb work/${label}${tag}_swap.glb work/${label}${tag}_lod0.glb Colloidal_A,ColloidalHead_A 2>&1 | grep -v Warn
[ "${3:-}" == final ] || exit 0
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$R/tools/build_actor_lods.py" -- "$PWD/work/${label}${tag}_lod0.glb" "$PWD/work/${label}${tag}_lods.glb" --mesh-node Colloidal --max-influences 4 2>&1 </dev/null | grep -E "LOD triangles|Error"
$G -W ignore $CW/shrink_shadow_lods.py work/${label}${tag}_lods.glb work/${label}${tag}_sf.glb Colloidal 2>&1 | grep -v Warn | tail -1 | cut -c1-160
$G -W ignore scripts/carry_variants.py work/${label}${tag}_sf.glb 2>&1 | grep -v Warn
$G -W ignore $CW/fix_winding.py work/${label}${tag}_sf.glb work/${label}${tag}_wound.glb 2>&1 | grep -v Warn | tail -1 | cut -c1-120
$G -W ignore scripts/compact.py work/${label}${tag}_wound.glb 2>&1 | grep -v Warn
cp work/${label}${tag}_wound.glb export/mm9_colloidalwarrior.glb
$G -W ignore "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_colloidalwarrior.glb 2>&1 | grep -v Warn | tail -1
python3 ../claude_shared/bone_length_audit.py export/mm9_colloidalwarrior.glb 2>&1 | tail -1
ls -la export/mm9_colloidalwarrior.glb
