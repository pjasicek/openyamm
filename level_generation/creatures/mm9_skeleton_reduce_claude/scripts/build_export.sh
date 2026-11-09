#!/usr/bin/env bash
# Candidate -> $E/mm9_skeleton.glb, the skeleton's own runtime chain after the clips (../mm9_skeleton_claude/scripts/
# build_runtime.sh): export_cand (linings back as reversed sheet copies on the dark texel; floor = source's lowest point)
# -> swap_lod0 into the installed source (materials, tier variants, region masks, eye emission, floor-fixed clips stay
# byte for byte; the dagger primitive kept whole) -> keep_normals (installed normals on vertices used only by kept faces)
# -> build_lods.py (tools/build_actor_lods.py, 4 influences, soles and crown protected) -> shrink_shadow_lods ->
# fix_lod_winding (the chain stops at LOD2 as installed) -> carry_variants -> winding check.
# Usage (project folder): EXPORT=export_x scripts/build_export.sh <tag>   (work/ladder_<LADDER>.blend holds Cand_<tag>)
set -euo pipefail
cd "$(dirname "$0")/.."; tag=$1; E=${EXPORT:-export}; mkdir -p $E
repo=/home/pjasicek/github/OpenYAMM; G="scripts/cap.sh $repo/level_generation/creatures/claude_shared/gltf_venv/bin/python -I"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
cp work/ladder_${LADDER}.blend work/ladder.blend
REA_TAG=$tag REA_CAND=Cand_$tag REA_NODE=Skel $BL -P scripts/export_cand.py 2>&1 | grep -E "LINING|FLOOR|EXPORTED|Error"
DROP_ATTRS=COLOR_0,COLOR_1 KEEP_PRIMS=Dagger $G scripts/swap_lod0.py before/mm9_skeleton.glb work/cand_export.glb $E/mm9_skeleton_lod0.glb Skel 2>&1 | grep -v prefix
$G scripts/keep_normals.py work/source_nolining.glb $E/mm9_skeleton_lod0.glb work/keep_r$tag.npy 2>&1 | grep -v prefix
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/$E/mm9_skeleton_lod0.glb" "$PWD/$E/mm9_skeleton_lods.glb" Skel 2>&1 </dev/null | grep -E "PROTECT|LOD triangles|Error"
$G scripts/shrink_shadow_lods.py $E/mm9_skeleton_lods.glb $E/mm9_skeleton_shadow.glb Skel 2>&1 | grep -v prefix | tail -1 | cut -c1-160
$G scripts/fix_lod_winding.py $E/mm9_skeleton_shadow.glb $E/mm9_skeleton.glb 2>&1 | grep -v prefix
$G scripts/carry_variants.py $E/mm9_skeleton.glb 2>&1 | grep -v prefix
for f in $E/mm9_skeleton_lods.geometry.glb $E/mm9_skeleton_shadow.glb; do if [[ -f $f ]]; then rm $f; fi; done
$G "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $E/mm9_skeleton.glb 2>&1 | grep -v prefix | tail -3
