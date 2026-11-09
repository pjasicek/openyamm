#!/usr/bin/env bash
# Fix pass: chart-guarded step -> runtime candidate. swap_mp.py (index buffers into the installed LOD0: every vertex attribute
# the installed bytes) -> build_lods.py (tools/build_actor_lods.py default ratios, 4 influences, soles and crown protected,
# points taken from the Blender import itself) -> the skeleton's shrink_shadow_lods -> fix_lod_winding (chain stops at LOD2, as
# installed) -> carry_variants -> check_winding -> same_parts. Usage (project folder): build_mp.sh <mp npz name, e.g. mp_m2_r80> <out dir>
set -euo pipefail
cd "$(dirname "$0")/.."; tag=$1; E=$2; mkdir -p $E
repo=/home/pjasicek/github/OpenYAMM; G="scripts/cap.sh $repo/level_generation/creatures/claude_shared/gltf_venv/bin/python -I -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
$G scripts/swap_mp.py before/mm9_skeleton.glb work/$tag.npz $E/mm9_skeleton_lod0.glb 2>&1 | grep -v prefix
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/$E/mm9_skeleton_lod0.glb" "$PWD/$E/mm9_skeleton_lods.glb" Skel 2>&1 </dev/null | grep -E "PROTECT|LOD triangles|Error"
$G scripts/shrink_shadow_lods.py $E/mm9_skeleton_lods.glb $E/mm9_skeleton_shadow.glb Skel 2>&1 | grep -v prefix | tail -1 | cut -c1-160
$G scripts/fix_lod_winding.py $E/mm9_skeleton_shadow.glb $E/mm9_skeleton.glb 2>&1 | grep -v prefix
$G scripts/carry_variants.py $E/mm9_skeleton.glb 2>&1 | grep -v prefix
for f in $E/mm9_skeleton_lods.geometry.glb $E/mm9_skeleton_shadow.glb; do if [[ -f $f ]]; then rm $f; fi; done
$G "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $E/mm9_skeleton.glb 2>&1 | grep -v prefix | tail -1
$G scripts/same_parts.py before/mm9_skeleton.glb $E/mm9_skeleton.glb 2>&1 | grep -v prefix | tail -1
