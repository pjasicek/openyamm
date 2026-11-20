#!/bin/bash
# heat -> weights -> glb -> clips -> half keys. Project folder. env MESH (default work/asm1.npz)
R=$PWD; G=../claude_shared/gltf_venv/bin/python; M=${MESH:-work/asm1.npz}
[ -n "$HEAT" ] && F='^(HEAT|Traceback)' scripts/run.sh heat_weights.py $R/$M $R/work/rig.json $R/work/heat.npz
python3 scripts/weights.py $M work/heat.npz work/rig.json work/finger_labels.npy work/weights.npz | tail -1 | cut -c1-200
$G -W ignore scripts/build_glb.py $M work/weights.npz work/body.glb 2>&1 | grep -v Unexpected | tail -1
$G -W ignore scripts/clips_es.py work/body.glb work/clips.glb scripts/roles_es.json work/clips.json 2>&1 | grep -E "Traceback|Error" 
$G -W ignore scripts/half_keys.py work/clips.glb work/half.glb 2>&1 | grep -E "Traceback|Error|HALF"
