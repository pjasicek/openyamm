#!/usr/bin/env bash
# Every gate of the brief on one candidate (project folder): faces-added-only, clips/images, UV escape, winding, lining
# poke (vertex), LOD heights, the creature's numeric gates (scripts/gates.sh) and the see-through gate on every clip with
# the visual lining poke check (ref = installed). Usage: scripts/final_gates.sh <glb> <tag>  -> review/gates_<tag>/
set -u
cd "$(dirname "$0")/.."
P=$PWD; glb=$(realpath $1); out=$P/review/gates_$2; mkdir -p $out
C="systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0"
V=../claude_shared/gltf_venv/bin/python
python3 scripts/prefix_check.py before/mm9_sven.glb $glb > $out/prefix.txt 2>&1
$V -W ignore scripts/same_clips.py before/mm9_sven.glb $glb > $out/same_clips_direct.txt 2>&1
$C python3 ../claude_shared/reduction_uv_audit.py $glb before/mm9_sven.glb --json $out/uv_audit.json > $out/uv_audit.txt 2>&1
$C python3 ../claude_shared/reduction_uv_audit.py before/mm9_sven.glb before/mm9_sven.glb > $out/uv_audit_installed.txt 2>&1
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding_direct.txt 2>&1
$C python3 scripts/lining_gate.py $glb before/mm9_sven.glb $out/lining_gate.json 10 > $out/lining_gate.txt 2>&1
$C python3 scripts/lod_heights.py before/mm9_sven.glb $glb $out/lod_heights.json > $out/lod_heights.txt 2>&1
scripts/gates.sh $glb $2
scripts/bl.sh $out/see_through.log level_generation/creatures/mm9_sven_lining_claude/scripts/see_through_gate.py $glb \
  $out/see_through.json step=4 px_mm=4 shots=2 extra= pieces=1 ref=$P/before/mm9_sven.glb
echo FINAL_GATES_DONE > $out/final_done.txt
