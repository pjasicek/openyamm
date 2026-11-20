#!/bin/bash
# The see-through gate (PeasantM3's own see_through_gate.py, an identical copy here so it runs under this project's lease; the
# creature's README settings: every 3rd 30 fps frame of every clip + Running 12, 8 azimuths x level / 20 deg down, 3 mm px).
# Usage (project folder): scripts/see_through.sh <glb> <tag> -> review/gates_<tag>/see_through.json
set -u
cd "$(dirname "$0")/.."
R=/home/pjasicek/github/OpenYAMM; P=$R/level_generation/creatures/mm9_peasantm3_reduce_claude
glb=$(realpath $1); out=$P/review/gates_$2; mkdir -p $out; T=$(cat LEASE_TOKEN.txt | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")
cd $R && systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 tools/run_creature_blender.sh --token $T \
  level_generation/creatures/mm9_peasantm3_reduce_claude/scripts/see_through_gate.py $glb $out/see_through.json step=3 \
  extra=Running:12 > $out/see_through.log 2>&1
echo SEEDONE $?
