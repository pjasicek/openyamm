#!/bin/bash
# Arm/hand, jitter and sleeve-poke gates on a runtime GLB. Usage (project folder): v2/scripts/run_gates.sh <glb> <outdir>
set -e
G=$1; O=$2; mkdir -p $O
PY="systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 python3"
$PY v2/scripts/arm_hand_gate.py $G $O/arm.json --side "L= L " --side "R= R " --outer-only --exact > $O/arm.txt 2>&1
$PY v2/scripts/jitter_gate.py $G v2/work/mm9_pm4_clips.glb $O/jitter.json --side "L= L " --side "R= R " > $O/jitter.txt 2>&1
$PY scripts/sleeve_poke_gate.py $G $O/sleeve_poke.json > $O/sleeve_poke.txt 2>&1
grep -v "^ " $O/arm.txt | head -20; grep -i "fail\|pass" $O/jitter.txt | head -20; cat $O/sleeve_poke.txt | tail -15
