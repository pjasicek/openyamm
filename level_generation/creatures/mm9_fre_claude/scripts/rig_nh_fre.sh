#!/usr/bin/env bash
# Pass 7 (new head): rig + MM9 clips on work/nh/asm_nh.npz with work/nh/weights_nh.npz (scripts/nh_assemble.py) -> work/half.glb.
# Same steps as rig_fre.sh after the weights (build_glb_pf.py, clips_pf.py, finger_rest.py, arm_out.py, half_keys.py); r72's rig.json.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
$G -W ignore scripts/build_glb_pf.py work/nh/asm_nh.npz work/nh/weights_nh.npz work/body.glb 2>&1 | grep -E "Traceback|Error|GLB|CANCELLED|ZERO"
$G -W ignore scripts/clips_pf.py work/body.glb work/clips.glb ${ROLES:-scripts/roles_pf.json} work/clips.json 2>&1 | grep -E "Traceback|Error|CLIPS" | cut -c1-200
$G -W ignore scripts/finger_rest.py work/clips.glb work/clips_f.glb 2>&1 | grep -E "Traceback|Error|FINGER"
$G -W ignore scripts/arm_out.py work/clips_f.glb work/clips_o.glb R:${ARMDEG:-0} L:${ARMDEG:-0} 2>&1 | grep -E "Traceback|Error" || true
cp work/clips_o.glb work/clips_arm.glb
$G -W ignore scripts/half_keys.py work/clips_arm.glb work/half.glb 2>&1 | grep -E "Traceback|Error|HALF"
$G -W ignore scripts/half_keys.py work/clips_o.glb work/ref_half.glb 2>&1 | grep -E "Traceback|Error" || true
