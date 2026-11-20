#!/usr/bin/env bash
# Candidate -> export/mm9_giant.glb, the giant's own LOD chain (../mm9_giant_claude/scripts/rebuild.sh after the clips):
# export_cand (mallet sharp edges by angle) -> swap_lod0 into the installed source (materials, variants, tier heads,
# floor-fixed clips stay byte for byte) -> tools/build_actor_lods.py (4 influences) -> shrink_shadow_lods -> carry_variants
# -> fix_winding (as rebuild.sh) -> winding check. Usage (project folder): REA_BLEND=ladder_x.blend scripts/build_export.sh Cand_NN
set -euo pipefail
cd "$(dirname "$0")/.."; cand=$1
repo=/home/pjasicek/github/OpenYAMM; G="scripts/cap.sh $repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
REA_CAND=$cand REA_NODE=Giant $BL -P scripts/export_cand.py 2>&1 | grep -E "SHARP|EXPORTED|Error"
KEEP_PRIMS=${KEEP_PRIMS:-GiantHead_A,GiantMallet_A} $G scripts/swap_lod0.py before/mm9_giant.glb work/cand_export.glb export/mm9_giant_lod0.glb Giant
if [[ -n "${HEAD_NORMALS:-}" ]]; then $G scripts/copy_kept_normals.py before/mm9_giant.glb export/mm9_giant_lod0.glb export/mm9_giant_lod0.glb $HEAD_NORMALS; fi   # pass 2: the cut head keeps the face's source normals
if [[ -n "${NEW_MALLET:-}" ]]; then $G scripts/mallet_inject.py export/mm9_giant_lod0.glb export/mm9_giant_lod0.glb Giant | tail -1; fi   # pass 2: rebuilt low-poly mallet with baked maps
$BL --disable-autoexec --python "$repo/tools/build_actor_lods.py" -- "$PWD/export/mm9_giant_lod0.glb" "$PWD/export/mm9_giant_lods.glb" --mesh-node Giant --max-influences 4 2>&1 </dev/null | grep -E "LOD triangles|Error"
$G scripts/shrink_shadow_lods.py export/mm9_giant_lods.glb export/mm9_giant.glb Giant 2>&1 | tail -1 | cut -c1-160
$G scripts/carry_variants.py export/mm9_giant.glb
$G scripts/fix_winding.py export/mm9_giant.glb work/wound.glb 2>&1 | tail -1 | cut -c1-120; mv work/wound.glb export/mm9_giant.glb   # as rebuild.sh: collapsed far-LOD studs
if [[ -f export/mm9_giant_lods.geometry.glb ]]; then rm export/mm9_giant_lods.geometry.glb; fi
$G "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_giant.glb | tail -1
