#!/usr/bin/env bash
# Rebuild the test chain with Blender directly (the project lock may be held by this agent's own long UV run)
set -e
BL=/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/e3a0eb70-7038-4872-820e-174fbf0faa9c/scratchpad/bl.sh; H=$PWD; G=../claude_shared/gltf_venv/bin/python; UVB=${1:-uv.blend}
$BL scripts/finish_skel.py -- $H/work/$UVB $H/work/final.blend $H/work/hand_poses.json | grep -E '^(FACES|FIST|THUMB|SCIMITAR)|Error|Traceback|line ' | cut -c1-200
$BL scripts/dump_faces.py -- $H/work/final.blend $H/work/faces.npz | grep -E 'Error' || true
$BL scripts/export_skel.py -- $H/work/final.blend $H/work/skel_body_tex.glb | grep -E 'LIFT|Error' | cut -c1-200
$BL scripts/dump_pid.py -- $H/work/final.blend $H/work/pid_dump.npz | grep -E 'Error' || true
$G scripts/clips_mm9.py work/skel_body_tex.glb work/skel_clips.glb scripts/roles_skel.json work/clips.json 2>&1 | tail -1 | cut -c1-30
$G scripts/finger_keys.py work/skel_clips.glb work/skel_final_clips.glb work/hand_poses.json 2>&1 | tail -1
