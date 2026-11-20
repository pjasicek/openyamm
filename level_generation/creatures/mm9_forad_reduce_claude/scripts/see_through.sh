#!/bin/bash
# The see-through gate (the PeasantDM2 creature see_through_gate.py, copied here so it runs under this project's lease) on one GLB.
# Usage (project folder): scripts/see_through.sh <glb> <tag> -> review/gates_<tag>/see_through.json
set -u
cd "$(dirname "$0")/.."
R=/home/pjasicek/github/OpenYAMM; P=$R/level_generation/creatures/mm9_forad_reduce_claude
glb=$(realpath $1); out=$P/review/gates_$2; mkdir -p $out; T=$(cat LEASE_TOKEN.txt)
cd $R && systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 tools/run_creature_blender.sh --token $T \
  level_generation/creatures/mm9_forad_reduce_claude/scripts/see_through_gate.py $glb $out/see_through.json > $out/see_through.log 2>&1
echo SEEDONE $?
# Forad's own sleeve gate (v2/scripts/sleeve_gate.py, copied: bracer see-through and forearm inside the bracer, every clip at 48 fps)
cd $R && systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 tools/run_creature_blender.sh --token $T \
  level_generation/creatures/mm9_forad_reduce_claude/scripts/sleeve_gate_forad.py $glb $out/sleeve_gate.json Bip01 > $out/sleeve_gate.log 2>&1
echo SLEEVEDONE $?
