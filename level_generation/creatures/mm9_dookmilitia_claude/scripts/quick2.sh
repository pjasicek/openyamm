#!/bin/bash
# textured export -> clips -> fingers -> half keys. Project folder.
R=$PWD; G=$R/../claude_shared/gltf_venv/bin/python
F='^(LIFT|EXPORTED)' scripts/run.sh export_dook.py $R/work/${BLEND:-final_v1.blend} $R/work/dook_body.glb
$G scripts/clips_mm9.py work/dook_body.glb work/dook_clips0.glb scripts/roles_dook.json work/clips.json 2>&1 | grep -v Unexpected | cut -c1-160
$G scripts/finger_keys.py work/dook_clips0.glb work/dook_clips1.glb work/hand_poses.json 2>&1 | tail -1
$G scripts/half_keys.py work/dook_clips1.glb work/dook_clips2.glb 2>&1 | tail -1
