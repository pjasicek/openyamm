#!/bin/bash
# The see-through gate (PeasantM2d's see_through_gate.py, copied here; head zone = materials containing "Head") on one GLB.
# Usage (project folder): scripts/see_through.sh <glb> <tag> [name, default see_through] [key=value ...]
#   -> review/gates_<tag>/<name>.json. PeasantM1d runs: name st_main with step=9 clips=<all but Conv5>, st_conv5 with
#   step=45 clips=Conv5 (the full step-3 pass took ~5 h per GLB: 22 s Conv5, 16 views).
set -u
cd "$(dirname "$0")/.."
R=/home/pjasicek/github/OpenYAMM; P=$R/level_generation/creatures/mm9_bjarni_reduce_claude
glb=$(realpath $1); out=$P/review/gates_$2; name=${3:-see_through}; shift 3 2>/dev/null || shift $#; mkdir -p $out; T=$(cat LEASE_TOKEN.txt)
cd $R && flock /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_bjarni_reduce_claude/work/blender.lock systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 tools/run_creature_blender.sh --token $T \
  level_generation/creatures/mm9_bjarni_reduce_claude/scripts/see_through_gate.py $glb $out/$name.json "$@" > $out/$name.log 2>&1
echo SEEDONE $name $?
