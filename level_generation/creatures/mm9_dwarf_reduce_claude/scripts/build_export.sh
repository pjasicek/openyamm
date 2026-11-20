#!/usr/bin/env bash
# Candidate -> $E/mm9_dwarf.glb, the dwarf's own LOD chain (../mm9_dwarf_claude/scripts/rebuild.sh after the clips):
# export_cand (floor = source's lowest point) -> swap_lod0 into the installed source (materials, tier variants, region
# masks, floor-fixed clips stay byte for byte) -> build_lods.py (tools/build_actor_lods.py, 4 influences, spike/horn tips/soles protected) -> shrink_shadow_lods ->
# carry_variants -> winding check. keep_normals.py after the swap: source normals on the kept surface (axe edges). Usage (project folder): REA_BLEND=ladder_x.blend scripts/build_export.sh Cand_NN
set -euo pipefail
cd "$(dirname "$0")/.."; cand=$1; E=${EXPORT:-export}; mkdir -p $E
repo=/home/pjasicek/github/OpenYAMM; G="scripts/cap.sh $repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
REA_CAND=$cand REA_NODE=Dwarf $BL -P scripts/export_cand.py 2>&1 | grep -E "FLOOR|EXPORTED|Error"
KEEP_PRIMS=DwarfWeapon $G scripts/swap_lod0.py before/mm9_dwarf.glb work/cand_export.glb $E/mm9_dwarf_lod0.glb Dwarf 2>&1 | grep -v Warn
$G scripts/keep_normals.py before/mm9_dwarf.glb $E/mm9_dwarf_lod0.glb ${REA_KEEP:-work/keep_d_lock.npy} 2>&1 | grep -v Warn
$BL --disable-autoexec --python scripts/build_lods.py -- "$PWD/$E/mm9_dwarf_lod0.glb" "$PWD/$E/mm9_dwarf_lods.glb" Dwarf 2>&1 </dev/null | grep -E "PROTECT|LOD triangles|Error"
$G scripts/shrink_shadow_lods.py $E/mm9_dwarf_lods.glb $E/mm9_dwarf.glb Dwarf 2>&1 | grep -v Warn | tail -1 | cut -c1-160
$G scripts/carry_variants.py $E/mm9_dwarf.glb 2>&1 | grep -v Warn
if [[ -f $E/mm9_dwarf_lods.geometry.glb ]]; then rm $E/mm9_dwarf_lods.geometry.glb; fi
$G "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $E/mm9_dwarf.glb 2>&1 | tail -1
