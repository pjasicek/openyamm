#!/usr/bin/env bash
# Fix-pass build: work/<tag>.npz (mpqem.py: index buffers into the installed LOD0's own vertices, so positions, normals, UVs,
# joints and weights stay the installed ones) -> swap_mp.py -> mallet_inject.py (rebuilt mallet + its baked maps) ->
# tools/build_actor_lods.py (4 influences) -> shrink_shadow_lods -> carry_variants -> fix_winding -> check_winding ->
# claude_shared/reduction_uv_audit.py. Usage (project folder): scripts/build_mp.sh <tag, e.g. mp_f_r45>
set -euo pipefail
cd "$(dirname "$0")/.."; tag=$1; repo=/home/pjasicek/github/OpenYAMM
G="scripts/cap.sh $repo/level_generation/creatures/claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
$G scripts/swap_mp.py before/mm9_giant.glb work/$tag.npz export/mm9_giant_lod0.glb
$G scripts/mallet_inject.py export/mm9_giant_lod0.glb export/mm9_giant_lod0.glb Giant | tail -1
$BL --disable-autoexec --python "$repo/tools/build_actor_lods.py" -- "$PWD/export/mm9_giant_lod0.glb" "$PWD/export/mm9_giant_lods.glb" --mesh-node Giant --max-influences 4 2>&1 </dev/null | grep -E "LOD triangles|Error"
$G scripts/shrink_shadow_lods.py export/mm9_giant_lods.glb export/mm9_giant.glb Giant 2>&1 | tail -1 | cut -c1-160
$G scripts/carry_variants.py export/mm9_giant.glb
$G scripts/fix_winding.py export/mm9_giant.glb work/wound.glb 2>&1 | tail -1 | cut -c1-120; mv work/wound.glb export/mm9_giant.glb
rm -f export/mm9_giant_lods.glb export/mm9_giant_lods.geometry.glb
$G "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_giant.glb | tail -1
mkdir -p review/uv_audit_fix
$G ../claude_shared/reduction_uv_audit.py export/mm9_giant.glb before/mm9_giant.glb --json review/uv_audit_fix/audit_$tag.json > review/uv_audit_fix/audit_$tag.txt 2>&1; grep LOD0 review/uv_audit_fix/audit_$tag.txt
