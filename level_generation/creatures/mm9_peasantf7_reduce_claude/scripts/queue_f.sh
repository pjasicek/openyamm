#!/bin/bash
# One-Blender queue for candidate f r45 (export/mm9_peasantf7.glb): ladder metrics, LOD check, see-through (installed, f45).
cd "$(dirname "$0")/.."
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
cp work/mesh_f_r45.npz work/mesh_r45.npz
REA_INFLUENCES=4 REA_METHOD=texture REA_RATIOS=0.45 $BL -P scripts/reduce_ladder.py > work/ladder_f.log 2>&1
REA_HEIGHT_M=1.758 scripts/cap.sh python3 scripts/compare_ladder.py > work/compare_f.log 2>&1
cp work/selection.json work/selection_f.json; cp review/ladder_sheet.png review/ladder_sheet_f.png
rm -f review/gates_f45/bl_done.txt review/gates_before/bl_done.txt
NO_ST=1 scripts/blender_gates.sh export/mm9_peasantf7.glb f45
NO_LOD=1 ST_ARGS=step=6 scripts/blender_gates.sh before/mm9_peasantf7.glb before
NO_LOD=1 ST_ARGS=step=6 scripts/blender_gates.sh export/mm9_peasantf7.glb f45
echo QUEUEDONE
