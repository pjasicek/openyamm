#!/bin/bash
# quick untextured viewer build: weights -> glb -> clips -> viewer. Project folder. Usage scripts/quick.sh <rev>
. scripts/env.sh
$G scripts/weights_liz.py work/heat2.npz work/w2.npz 2>&1 | tail -1 | cut -c1-140
$G scripts/build_glb.py work/joined.npz work/w2.npz work/q2.glb 2>&1 | tail -1
$G scripts/clips_mm9.py work/q2.glb work/q2_clips.glb scripts/roles_liz.json work/clips.json 2>&1 | tail -1 | cut -c1-60
$G scripts/half_keys.py work/q2_clips.glb work/q3.glb 2>&1 | tail -1
$G scripts/make_viewer_manifest.py $1 liz_a="Lizard-Orc"=work/q3.glb 2>&1 | tail -1 | cut -c1-100
