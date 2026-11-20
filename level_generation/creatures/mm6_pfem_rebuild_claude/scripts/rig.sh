#!/usr/bin/env bash
# Rig + clips (project folder): scripts/rig.sh -> work/half.glb (fit -> weights -> skinned GLB from the UV mesh -> MM9 clips -> relaxed fingers -> half joints)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"
G=$here/../claude_shared/gltf_venv/bin/python
# ASM=work/asm3.npz: the bodice un-turned (torso_unturn.py); KEEPFIT=1 keeps work/rig.json (the joints) as fitted
if [ -z "${KEEPFIT:-}" ]; then $G -W ignore scripts/fit_rig.py ${ASM:-work/asm2.npz} source/mm9/pf1b.glb work/rig.json 2>&1 | grep -E "Traceback|Error|MOVES"; fi
$G -W ignore scripts/weights.py ${ASM:-work/asm2.npz} work/rig.json work/weights.npz 2>&1 | grep -E "Traceback|Error|WEIGHTS"
# WKEEP=<installed weights npz>: new weights only on the moved bodice (weights_merge.py)
if [ -n "${WKEEP:-}" ]; then $G -W ignore scripts/weights_merge.py work/weights.npz "$WKEEP" ${ASM:-work/asm2.npz} work/weights.npz 2>&1 | grep -E "Traceback|Error|WEIGHTS"; fi
$G -W ignore scripts/build_glb.py ${MESH:-work/uv.npz} work/weights.npz work/body.glb 2>&1 | grep -E "Traceback|Error|GLB"
$G -W ignore scripts/clips.py work/body.glb work/clips.glb ${ROLES:-scripts/roles.json} work/clips.json 2>&1 | grep -E "Traceback|Error|CLIPS" | cut -c1-300
$G -W ignore scripts/wrist_relax.py work/clips.glb work/clips_w.glb ${WRIST:-0.5} 2>&1 | grep -E "Traceback|Error|WRIST"
CURL=${CURL:-1.6} $G -W ignore scripts/finger_rest.py work/clips_w.glb work/clips_f.glb 2>&1 | grep -E "Traceback|Error|FINGER"
CLIPS=${ARMCLIPS:-Standing,Fidget,Attack,Hit,Death,Dead} $G -W ignore scripts/arm_out.py work/clips_f.glb work/clips_o.glb ${ARMOUT:-L:5 R:2} 2>&1 | grep -E "Traceback|Error" || true
prev=work/clips_o.glb
if [ -f scripts/hand_rest.txt ]; then k=0
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue; k=$((k + 1))
    eval "$G -W ignore scripts/hand_rest.py $prev work/rest$k.glb $line" 2>&1 | grep -E "Traceback|Error|REST" | cut -c1-200 || true
    prev=work/rest$k.glb
  done < scripts/hand_rest.txt
fi
$G -W ignore scripts/half_keys.py $prev work/half.glb 2>&1 | grep -E "Traceback|Error|HALF"
