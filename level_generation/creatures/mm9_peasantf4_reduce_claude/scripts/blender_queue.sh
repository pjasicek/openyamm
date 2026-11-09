#!/bin/bash
# One Blender at a time for a candidate: see-through gate, LOD check, magenta back faces. Usage: scripts/blender_queue.sh <glb> <tag>
cd "$(dirname "$0")/.."
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
g=$1; T=$2; O=review/gates_$T; mkdir -p $O
$BL --python ../mm9_peasantf4_claude/scripts/see_through_gate.py -- "$PWD/$g" "$PWD/$O/see_through.json" > $O/see.log 2>&1; echo SEE $?
REA_NODE=PeasantF4 $BL --python scripts/lod_check.py -- "$PWD/$g" gates_$T > $O/lod_check.log 2>&1; echo LOD $?
scripts/diag_backfaces.sh $g $T; echo DIAG $?
