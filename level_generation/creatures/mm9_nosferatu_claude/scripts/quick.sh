#!/bin/bash
# geometry -> rig -> first runtime GLB work/q.glb (no textures). Usage (project folder): scripts/quick.sh [clips]
. scripts/env.sh
A=${ASM:-work/asm1.npz}
$PYG scripts/fit_rig.py $A source/n1/n1.glb work/rig.json 2>&1 | grep -E "Traceback|Error|shoulder" | cut -c1-200
$PYG scripts/weights.py $A work/rig.json work/finger_labels.npy work/weights.npz | tail -1 | cut -c1-200
$PYG -W ignore scripts/build_glb.py $A work/weights.npz work/body.glb 2>&1 | tail -1
$PYG -W ignore scripts/clips_mm9.py work/body.glb work/clips.glb scripts/roles.json work/clips.json 2>&1 | grep -E "Traceback|Error" 
$PYG -W ignore scripts/half_keys.py work/clips.glb work/half.glb 2>&1 | grep -E "Traceback|Error"
$PYG -W ignore scripts/finger_keys.py work/half.glb work/fing.glb 2>&1 | grep -E "Traceback|Error"
$PYG -W ignore scripts/robe_keys.py work/fing.glb work/q.glb 2>&1 | tail -1
