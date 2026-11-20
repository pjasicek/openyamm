#!/bin/bash
# The creature's see-through gate (../mm9_peasanthof_claude/scripts/see_through_gate.py, read-only use; every 6th 30 fps frame,
# 16 views, as its r7/r8 runs) on one GLB; one Blender at a time (work/blender.lock).
# Usage (project folder): M=1|2 scripts/see_through.sh <glb> <tag> -> review/hof$M/gates_<tag>/see_through.json
set -u
cd "$(dirname "$0")/.."; : "${M:?M=1|2}"
glb=$(realpath $1); out=$PWD/review/hof$M/gates_$2; mkdir -p $out
flock work/blender.lock scripts/cap.sh /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python ../mm9_peasanthof_claude/scripts/see_through_gate.py -- $glb $out/see_through.json step=6 > $out/see_through.log 2>&1
echo SEEDONE $?
