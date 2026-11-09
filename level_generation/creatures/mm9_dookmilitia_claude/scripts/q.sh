#!/bin/bash
# rig -> hands -> quick -> collapse + skirt gates. Project folder. FROM=rig to start at the rig step
R=$PWD; G=$R/../claude_shared/gltf_venv/bin/python
F='^(RIG skirt)' W=120 scripts/run.sh rig_dook.py $R/work/graft_v1.blend $R/work/rig_v1.blend $R/work/rig_v1.json
F='^(XX)' scripts/run.sh graft_hands.py $R/scripts/graft_dook.json
bash scripts/quick.sh 2>&1 | grep -E "Traceback|Error|SKIRT" | cut -c1-200
($G scripts/collapse_gate.py work/quick_skirt.glb review/gates0/collapse.json > review/gates0/collapse.txt 2>&1 &  $G scripts/skirt_gate.py work/quick_skirt.glb review/gates0/skirt.json > review/gates0/skirt.txt 2>&1 & wait)
