#!/bin/bash
# sym -> pivots -> quick glb -> clips -> helpers' keys -> collapse -> bone audit. Project folder.
R=$PWD; G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
[[ -n "$SKIP_S" ]] || F='^(SYM|NEWGROUP)' scripts/run.sh sym_giant.py $R/work/red_v1.blend $R/work/sym_v1.blend
F='^(MOVED)' scripts/run.sh move_joints.py $R/work/sym_v1.blend $R/work/piv_v1.blend $R/scripts/pivots_final.json
F='^(LIFT|EXPORTED)' scripts/run.sh export_quick.py $R/work/piv_v1.blend $R/work/quick_body.glb
$G scripts/clips_mm9.py work/quick_body.glb work/quick_clips0.glb scripts/roles_giant.json work/clips.json 2>&1 | grep -E 'Error|Traceback'
$G scripts/half_keys.py work/quick_clips0.glb work/quick_clips.glb 2>&1 | tail -1 | cut -c1-200
$G scripts/collapse_gate.py work/quick_clips.glb work/collapse1.json 2>&1 | grep -E 'face-frames|Error' | sed 's/  | exposed.*//; s/face-frames//; s/worst frame//' | cut -c1-230
python3 ../claude_shared/bone_length_audit.py work/quick_clips.glb | cut -c1-120
