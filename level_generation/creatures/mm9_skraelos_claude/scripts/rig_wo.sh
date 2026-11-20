#!/usr/bin/env bash
# Rig + clips on a mesh npz (project folder): scripts/rig_wo.sh <mesh npz (asm or uv)> -> work/half.glb (+ work/ref_half.glb without arm corrections)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
M=${1:-work/asm_f.npz}; A=${ASM:-work/asm_f.npz}
HEAD_POS=${HEAD_POS:-0,-0.215,0.515} $G -W ignore scripts/fit_rig_wo.py $A source/mm9/wyrd_old/wyrd_old.glb work/rig.json 2>&1 | grep -E "Traceback|Error|RIG|HEAD" | cut -c1-160
$G -W ignore scripts/weights_wo.py $A work/mm9.npz work/rig.json work/weights.npz 2>&1 | grep -E "Traceback|Error|WEIGHTS|HOOD|mirror|SEAM"
$G -W ignore scripts/build_glb_wo.py $M work/weights.npz work/body.glb 2>&1 | grep -E "Traceback|Error|GLB"
$G -W ignore scripts/clips_pf.py work/body.glb work/clips.glb ${ROLES:-scripts/roles_wo.json} work/clips.json 2>&1 | grep -E "Traceback|Error|CLIPS" | cut -c1-200
$G -W ignore scripts/finger_rest.py work/clips.glb work/clips_f.glb 2>&1 | grep -E "Traceback|Error|FINGER"
$G -W ignore scripts/arm_out.py work/clips_f.glb work/clips_o.glb R:${ARMDEG:-3} L:${ARMDEG:-3} 2>&1 | grep -E "Traceback|Error" || true
prev=work/clips_o.glb
if [ -f scripts/arm_jobs_wo.txt ]; then k=0
  while read -r clips cap sig; do
    [ -z "$clips" ] && continue; [[ "$clips" == \#* ]] && continue; k=$((k + 1))
    $G -W ignore scripts/arm_clear.py work/clips_o.glb work/cl_c$k.glb --side L=' L ' --side R=' R ' --clips $clips --outer-only --max-deg $cap --sigma 2.0 --root Pelvis 2>&1 | grep -E "Traceback|Error" || true
    FADE=0.16 $G -W ignore scripts/arm_soft.py $prev work/cl_c$k.glb work/cl_a$k.glb $cap $sig $clips 2>&1 | grep -E "Traceback|Error" || true
    prev=work/cl_a$k.glb
  done < scripts/arm_jobs_wo.txt
fi
if [ -f scripts/hand_rest_wo.txt ]; then k=0
  while read -r line; do
    [ -z "$line" ] && continue; k=$((k + 1))
    eval "$G -W ignore scripts/hand_rest.py $prev work/hr_$k.glb $line" 2>&1 | grep -E "Traceback|Error" || true
    prev=work/hr_$k.glb
  done < scripts/hand_rest_wo.txt
fi
if [ -f scripts/arm_clip_wo.txt ]; then $G -W ignore scripts/arm_out_clip.py $prev work/clips_ac.glb $(cat scripts/arm_clip_wo.txt) | tail -1; prev=work/clips_ac.glb; fi
cp $prev work/clips_arm.glb
$G -W ignore scripts/half_keys.py work/clips_arm.glb work/half.glb 2>&1 | grep -E "Traceback|Error|HALF"
$G -W ignore scripts/half_keys.py work/clips_o.glb work/ref_half.glb 2>&1 | grep -E "Traceback|Error" || true
