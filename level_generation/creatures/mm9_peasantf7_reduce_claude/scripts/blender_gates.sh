#!/bin/bash
# The Blender part of gates.sh (see-through double=1, lod_check) for one GLB; run one at a time. Usage: blender_gates.sh <glb> <tag>
cd "$(dirname "$0")/.."; glb=$(realpath $1); out=review/gates_$2; mkdir -p $out
F=/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_peasantf7_claude
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
[[ "${NO_LOD:-0}" == 1 ]] || REA_NODE=PeasantF7 $BL -P scripts/lod_check.py -- $glb $2 > $out/lod_check.log 2>&1
[[ "${NO_ST:-0}" == 1 ]] || $BL --python scripts/see_through_gate.py -- $glb $(realpath $out)/see_through.json double=1 ${ST_ARGS:-} > $out/see_through.txt 2>&1
echo BLDONE > $out/bl_done.txt
