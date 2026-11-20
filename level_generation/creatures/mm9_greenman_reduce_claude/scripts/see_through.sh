#!/bin/bash
# The Green Man's see-through gate (../mm9_greenman_claude/scripts/see_through_gate.py, copied so it runs under this project's
# lease) on one GLB with the creature's r3 sampling (5 clips, every 8th frame, 16 views, 3 mm px).
# Usage (project folder): scripts/see_through.sh <glb> <tag> -> review/gates_<tag>/see_through.json
set -u
cd "$(dirname "$0")/.."
R=/home/pjasicek/github/OpenYAMM; P=$R/level_generation/creatures/mm9_greenman_reduce_claude
glb=$(realpath $1); out=$P/review/gates_$2; mkdir -p $out; T=$(python3 -c "import json;print(json.load(open('LEASE_TOKEN.txt'))['token'])")
cd $R && systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 tools/run_creature_blender.sh --token $T \
  level_generation/creatures/mm9_greenman_reduce_claude/scripts/see_through_gate.py $glb $out/see_through.json \
  clips=Standing,Walking,Running,Fidget,Death step=8 > $out/see_through.log 2>&1
echo SEEDONE $?
