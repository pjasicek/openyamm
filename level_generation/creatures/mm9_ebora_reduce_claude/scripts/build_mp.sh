#!/usr/bin/env bash
# Ebora fix-pass build (after mm9_giant_reduce_claude/scripts/build_mp.sh): work/<tag>.npz (mpqem.py: index buffers into the
# installed LOD0's own vertices, so positions, normals, UVs, joints and weights stay the installed ones) -> swap_mp.py ->
# tools/build_actor_lods.py (Ebora's ratios, 4 influences) -> shrink_shadow_lods -> carry_variants -> Ebora's fix_winding ->
# compact -> check_winding, bone length -> claude_shared/reduction_uv_audit.py. Usage (project folder): scripts/build_mp.sh <tag>
set -euo pipefail
cd "$(dirname "$0")/.."; tag=$1; repo=/home/pjasicek/github/OpenYAMM
G="scripts/cap.sh $repo/level_generation/creatures/claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
$G scripts/swap_mp.py before/mm9_ebora.glb work/$tag.npz work/${tag}_lod0.glb
$BL --disable-autoexec --python "$repo/tools/build_actor_lods.py" -- "$PWD/work/${tag}_lod0.glb" "$PWD/work/${tag}_lods.glb" --mesh-node Ebora --max-influences 4 2>&1 </dev/null | grep -E "LOD triangles|Error"
$G ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py work/${tag}_lods.glb work/${tag}_sf.glb Ebora 2>&1 | tail -1 | cut -c1-160
$G scripts/carry_variants.py work/${tag}_sf.glb
$G ../mm9_ebora_claude/scripts/fix_winding.py work/${tag}_sf.glb export/mm9_ebora.glb 2>&1 | tail -1 | cut -c1-120
$G scripts/compact.py export/mm9_ebora.glb
$G "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_ebora.glb | tail -1
$G ../claude_shared/bone_length_audit.py export/mm9_ebora.glb | tail -1
mkdir -p review/uv_audit_fix
$G ../claude_shared/reduction_uv_audit.py export/mm9_ebora.glb before/mm9_ebora.glb --json review/uv_audit_fix/audit_$tag.json > review/uv_audit_fix/audit_$tag.txt 2>&1; grep LOD0 review/uv_audit_fix/audit_$tag.txt
