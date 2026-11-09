#!/bin/bash
# fist blend -> quick glb -> MM9 clips -> finger keys (fist, left flexion) -> helpers' keys -> bone audit. Project folder. BLEND=fist_v1.blend
R=$PWD; G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python; B=${BLEND:-fist_v1.blend}
F='^(LIFT|EXPORTED)' scripts/run.sh export_quick.py $R/work/$B $R/work/quick_body.glb
$G scripts/clips_mm9.py work/quick_body.glb work/quick_clips0.glb scripts/roles_giant.json work/clips.json 2>&1 | grep -E 'Error|Traceback'
$G scripts/finger_keys_giant.py work/quick_clips0.glb work/quick_clips1.glb work/hand_poses.json 2>&1 | grep -E 'FINGERKEYS|Error|Traceback'
$G scripts/half_keys.py work/quick_clips1.glb work/quick_clips.glb 2>&1 | tail -1 | cut -c1-200
$G scripts/half_keys.py work/quick_clips0.glb work/quick_ref.glb 2>&1 | tail -1 | cut -c1-200     # jitter reference: MM9's clips, same helpers
python3 ../claude_shared/bone_length_audit.py work/quick_clips.glb | cut -c1-120
