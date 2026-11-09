#!/usr/bin/env bash
# Rig + clips on a mesh npz (project folder): scripts/rig_wo.sh <mesh npz (asm or uv)> -> work/half.glb (+ work/ref_half.glb without arm corrections)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
M=${1:-work/asm.npz}; A=${ASM:-work/asm.npz}
HEAD_POS=${HEAD_POS:-mm9} $G -W ignore scripts/fit_rig_sc.py $A source/mm9/scholar/scholar.glb work/rig.json 2>&1 | grep -E "Traceback|Error|RIG|HEAD" | cut -c1-160
$G -W ignore scripts/weights_sc.py $A work/mm9.npz work/rig.json work/weights.npz 2>&1 | grep -E "Traceback|Error|WEIGHTS|HOOD|mirror|SEAM"
$G -W ignore scripts/build_glb_sc.py $M work/weights.npz work/body.glb 2>&1 | grep -E "Traceback|Error|GLB"
$G -W ignore scripts/clips_pf.py work/body.glb work/clips.glb ${ROLES:-scripts/roles_sc.json} work/clips.json 2>&1 | grep -E "Traceback|Error|CLIPS" | cut -c1-200
$G -W ignore scripts/finger_rest.py work/clips.glb work/clips_f.glb 2>&1 | grep -E "Traceback|Error|FINGER"
$G -W ignore scripts/arm_out.py work/clips_f.glb work/clips_o.glb R:${ARMDEG:-0} L:${ARMDEG:-0} 2>&1 | grep -E "Traceback|Error" || true
prev=work/clips_o.glb
if [ -f scripts/arm_jobs_sc.txt ]; then k=0
  while read -r clips cap sig; do
    [ -z "$clips" ] && continue; [[ "$clips" == \#* ]] && continue; k=$((k + 1))
    $G -W ignore scripts/arm_clear.py work/clips_o.glb work/cl_c$k.glb --side L=' L ' --side R=' R ' --clips $clips --outer-only --max-deg $cap --sigma 2.0 --root Spine 2>&1 | grep -E "Traceback|Error" || true
    FADE=0.16 $G -W ignore scripts/arm_soft.py $prev work/cl_c$k.glb work/cl_a$k.glb $cap $sig $clips 2>&1 | grep -E "Traceback|Error" || true
    prev=work/cl_a$k.glb
  done < scripts/arm_jobs_sc.txt
fi
if [ -f scripts/arm_clip_sc.txt ]; then $G -W ignore scripts/arm_out_clip.py $prev work/clips_ac.glb $(cat scripts/arm_clip_sc.txt) | tail -1; prev=work/clips_ac.glb; fi
if [ -f scripts/wrist_clamp_sc.txt ]; then $G -W ignore scripts/wrist_clamp.py $prev work/clips_wc.glb $(cat scripts/wrist_clamp_sc.txt) | tail -1; prev=work/clips_wc.glb; fi
cp $prev work/clips_arm.glb
$G -W ignore scripts/half_keys.py work/clips_arm.glb work/half.glb 2>&1 | grep -E "Traceback|Error|HALF"
$G -W ignore scripts/half_keys.py work/clips_o.glb work/ref_half.glb 2>&1 | grep -E "Traceback|Error" || true
