#!/usr/bin/env bash
# Candidate -> $E/mm9_wingedmutant.glb with the Winged Mutant's own runtime chain (../mm9_wingedmutant_claude/scripts/
# build_runtime.sh after prepare): export_cand (floor = source's lowest point) -> swap_lod0 into the installed source
# (materials, tier variants, region masks, hover-fixed clips, sockets stay byte for byte) -> keep_normals (source normals on
# the kept surface: face, eyes, teeth, body) -> build_lods.py (tools/build_actor_lods.py default ratios and influences, as the creature, death floor contacts protected)
# -> the creature's shrink_shadow_lods.py (wing shells stay in place) -> carry_variants -> the creature's fix_winding.py -> fix_lod_floor.py
# -> check_winding. Usage (project folder): REA_BLEND=ladder_x.blend REA_KEEP=work/keep_x.npy scripts/build_export.sh Cand_NN
set -euo pipefail
cd "$(dirname "$0")/.."; cand=$1; E=${EXPORT:-export}; mkdir -p $E
repo=/home/pjasicek/github/OpenYAMM; G="scripts/cap.sh $repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
N=mm9_wingedmutant
REA_CAND=$cand REA_NODE=Wmut $BL -P scripts/export_cand.py 2>&1 | grep -E "FLOOR|EXPORTED|Error"
$G scripts/swap_lod0.py before/$N.glb work/cand_export.glb $E/${N}_lod0.glb Wmut 2>&1 | grep -v Warn
NODE=Wmut $G scripts/keep_normals.py before/$N.glb $E/${N}_lod0.glb ${REA_KEEP:?keep npy} 2>&1 | grep -v Warn
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/$E/${N}_lod0.glb" "$PWD/$E/${N}_lods.glb" Wmut 2>&1 </dev/null | grep -E "PROTECT|LOD triangles|Error"
$G scripts/shrink_shadow_lods.py $E/${N}_lods.glb $E/${N}_shadow.glb Wmut 2>&1 | grep -v Warn | tail -1 | cut -c1-160
$G scripts/carry_variants.py $E/${N}_shadow.glb 2>&1 | grep -v Warn
$G scripts/fix_winding.py $E/${N}_shadow.glb $E/$N.glb 2>&1 | grep -v Warn | tail -2
scripts/cap.sh python3 scripts/fix_lod_floor.py $E/$N.glb
if [[ -f $E/${N}_lods.geometry.glb ]]; then rm $E/${N}_lods.geometry.glb; fi
$G "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $E/$N.glb 2>&1 | tail -1
