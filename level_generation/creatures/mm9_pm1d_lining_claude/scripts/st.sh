#!/bin/bash
# See-through gate at the 2026-11-02 sweep's settings (step 4, 4 mm pixels, 2 shots per zone, no extra frames) on one GLB,
# under the lease and the memory cap. Usage (any folder): scripts/st.sh <glb> <tag> [key=value ...] -> review/st_<tag>/see_through.json
set -u
cd "$(dirname "$0")/.."; P=$PWD; R=$(cd ../../.. && pwd)
glb=$(realpath $1); out=$P/review/st_$2; shift 2; mkdir -p $out; T=$(cat LEASE_TOKEN.txt)
cd $R && systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 tools/run_creature_blender.sh --token $T \
  level_generation/creatures/mm9_pm1d_lining_claude/scripts/see_through_gate.py $glb $out/see_through.json step=4 px_mm=4 shots=2 extra= "$@" > $out/run.log 2>&1
echo SEEDONE $? >> $out/run.log
