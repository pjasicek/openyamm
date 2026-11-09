#!/bin/bash
# fingers -> heat -> weights -> quick glb -> clips. Project folder. Env PIVOTS, PASSES.
. scripts/env.sh
$G scripts/fingers.py work/body_only.npz 2>&1 | grep -E '^Finger|Error'
$G scripts/prep_bones.py work/body_only.npz 2>/dev/null
F='^HEAT' scripts/run_b.sh heat.py $P/work/body_only.npz $P/work/heat2.npz
$G scripts/weights.py work/joined.npz work/heat2.npz work/finger_labels.npy work/w2.npz 2>&1 | grep -E 'influences|Error|Trace'
$G scripts/build_glb.py work/joined.npz work/w2.npz work/q2.glb 2>&1 | tail -1
$G scripts/clips_mm9.py work/q2.glb work/q2_clips.glb scripts/roles_trog.json work/clips.json 2>&1 | tail -1 | cut -c1-120
