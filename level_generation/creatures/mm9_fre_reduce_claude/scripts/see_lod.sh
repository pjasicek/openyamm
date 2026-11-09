#!/bin/bash
# Blender part of gates.sh --see (Fre's see_through_gate.py and lod_check.py), one Blender at a time. Usage: see_lod.sh <glb> <out dir> ...
set -u
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
while [[ $# -ge 2 ]]; do
  g=$1; O=$2; shift 2; mkdir -p $O
  $BL --python ../mm9_fre_claude/scripts/see_through_gate.py -- "$PWD/$g" "$PWD/$O/see_through.json" > $O/see.log 2>&1
  REA_NODE=Fre $BL --python scripts/lod_check.py -- "$PWD/$g" "$(basename $O)" > $O/lod_check.log 2>&1
  echo SEE_LOD DONE $O
done
