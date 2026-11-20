#!/bin/bash
# runtime build + arm/hand, prop and see-through gates (project folder): scripts/gates2.sh <out dir>
O=${1:-review/gates}; mkdir -p $O
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
[ -z "${NOBUILD:-}" ] && systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 scripts/build_runtime_sk.sh 2>&1 | grep -E "WINDING|Error|LOD tri"
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 $G -W ignore scripts/arm_hand_gate.py export/mm9_skraelos.glb $O/arm_hand.json --side L=" L " --side R=" R " --outer-only --exact 2>&1 | grep -v Unexpected | cut -c1-200 > $O/arm_hand.txt &
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 $G -W ignore scripts/prop_gate.py export/mm9_skraelos.glb $O/prop_gate.json 2>&1 | grep -v Unexpected > $O/prop_gate.txt &
wait
cat $O/arm_hand.txt $O/prop_gate.txt
echo GATES2 DONE
