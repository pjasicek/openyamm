#!/bin/bash
# run 2: weights -> mesh -> clips -> half keys (no bumps, flap, floor) and the collapse split on work/qc_half.glb. Project folder. Usage: scripts/quick_collapse.sh <tag> [clips]
. scripts/env.sh
$G scripts/weights_liz.py work/heat2.npz work/w2.npz 2>&1 | grep -E 'influences|Error|Trace' | cut -c1-120
$G scripts/assemble.py work/joined.npz work/w2.npz work/uv.npz work/final.npz work/final_w.npz scripts/tex_final.json 2>&1 | tail -1
$G scripts/build_glb.py work/final.npz work/final_w.npz work/body.glb 2>&1 | tail -1
$G scripts/clips_mm9.py work/body.glb work/raw_clips.glb scripts/roles_liz.json work/clips.json 2>&1 | grep -E 'Error|Trace'
$G scripts/finger_keys.py work/raw_clips.glb work/fist_clips.glb 2>&1 | grep -E 'Error|Trace'
$G scripts/half_keys.py work/fist_clips.glb work/qc_half.glb 2>&1 | tail -1
$G scripts/collapse_parts.py work/qc_half.glb work/qc_$1.txt ${2:-Death,Hit2,Death2,Dead,Walking,AttackMelee,Standing}
