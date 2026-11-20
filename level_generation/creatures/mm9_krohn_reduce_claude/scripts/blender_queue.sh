#!/bin/bash
# One Blender at a time (brief): see-through gate on the installed file and the candidate, then lod_check on both.
# Usage: scripts/blender_queue.sh <candidate glb> <tag>
cd "$(dirname "$0")/.."; HERE=$PWD; S=../mm9_krohn_claude/scripts
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
st() { mkdir -p review/gates_$2/see_through; $BL --python $S/see_through_gate.py -- $(realpath $1) $HERE/review/gates_$2/see_through/see_through.json \
  step=5 px_mm=4.5 clips=Standing,Walking,Running,Fidget,AttackMelee,Hit,Death > review/gates_$2/see_through_full.txt 2>&1
  grep SEE_THROUGH review/gates_$2/see_through_full.txt > review/gates_$2/see_through.txt; }
[[ -s review/gates_before/see_through.txt ]] || st before/mm9_krohn.glb before
st $1 $2
[[ -s work/lod_check_inst.json ]] || REA_NODE=Krohn $BL -P scripts/lod_check.py -- $HERE/before/mm9_krohn.glb inst > work/lod_check_inst.log 2>&1
REA_NODE=Krohn $BL -P scripts/lod_check.py -- $(realpath $1) $2 > work/lod_check_$2.log 2>&1
echo QDONE > work/queue_$2.done
