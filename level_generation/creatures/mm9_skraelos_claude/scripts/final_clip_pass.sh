#!/bin/bash
# clip-level pass after the final geometry/paint (project folder): rig + clips + arm offsets -> runtime + install -> arm, prop, jitter gates
set -u
O=${1:-review/gates_final}; mkdir -p $O
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
ASM=work/asm5.npz systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 scripts/rig_sk.sh work/uv_ln_tex.npz 2>&1 | grep -E "Error|Trace"
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 scripts/build_runtime_sk.sh ${INSTALL:---install} 2>&1 | grep -E "WINDING|Error|source"
NOBUILD=1 scripts/gates2.sh $O > /dev/null 2>&1
$G -W ignore scripts/jitter_gate.py work/clips_arm.glb work/clips.glb $O/jitter.json --side L=' L ' --side R=' R ' 2>&1 | grep -v Unexpected > $O/jitter.txt
grep -E "FAIL|JITTER" $O/jitter.txt | cut -c1-60; grep -E "Resurrect|Death|Fidget|Running|Hit|Talk" $O/arm_hand.txt | cut -c1-200; cat $O/prop_gate.txt | cut -c1-140
echo PASSDONE
