#!/bin/bash
# weights -> glb -> clips -> half keys. Project folder. env MESH (default work/asm1.npz)
G=../claude_shared/gltf_venv/bin/python; M=${MESH:-work/asm1.npz}
python3 scripts/weights.py work/asm2.npz work/mm9.npz work/rig.json work/weights.npz | tail -1 | cut -c1-200
$G -W ignore scripts/build_glb.py $M work/weights.npz work/body.glb 2>&1 | grep -v Unexpected | tail -1
$G -W ignore scripts/clips_mk.py work/body.glb work/clips.glb scripts/roles_mk.json work/clips.json 2>&1 | grep -E "Traceback|Error|CLIPS" | cut -c1-300
$G -W ignore scripts/half_keys.py work/clips.glb work/half.glb 2>&1 | grep -E "Traceback|Error|HALF"
