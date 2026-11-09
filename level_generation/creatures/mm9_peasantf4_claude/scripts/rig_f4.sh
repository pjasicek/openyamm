#!/usr/bin/env bash
# PF4 rig + clips on a mesh npz (project folder): scripts/rig_f4.sh <mesh npz (asm or uv)> -> work/half.glb (+ work/ref_half.glb)
# Weights: weights_pf4.py on the PF4 asm, then merge_weights_pf4.py puts PeasantF1's own weights back on every F1 vertex.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
M=${1:-work/asm_frozen.npz}
$G -W ignore scripts/fit_rig_pf.py work/asm_frozen.npz source/mm9/pf1b.glb work/rig.json 2>&1 | grep -E "Traceback|Error" | cut -c1-160 || true
$G -W ignore scripts/weights_pf3.py work/asm_frozen_f1.npz work/mm9.npz work/rig.json work/weights_f1chk.npz 2>&1 | grep -E "Traceback|Error" || true
$G -W ignore scripts/weights_pf4.py work/asm_frozen.npz work/mm9.npz work/rig.json work/weights_pf4raw.npz 2>&1 | grep -E "Traceback|Error|WEIGHTS"
python3 scripts/merge_weights_pf4.py work/weights_f1chk.npz work/weights_pf4raw.npz work/asm_frozen_f1.npz work/weights.npz work/asm_frozen.npz
$G -W ignore scripts/build_glb_pf.py $M work/weights.npz work/body.glb 2>&1 | grep -E "Traceback|Error|GLB|NOSE normal|RELAXED"
$G -W ignore scripts/clips_pf.py work/body.glb work/clips.glb ${ROLES:-scripts/roles_pf.json} work/clips.json 2>&1 | grep -E "Traceback|Error|CLIPS" | cut -c1-200
$G -W ignore scripts/finger_rest.py work/clips.glb work/clips_f.glb 2>&1 | grep -E "Traceback|Error|FINGER"
$G -W ignore scripts/arm_out.py work/clips_f.glb work/clips_o.glb R:${ARMDEG:-0} L:${ARMDEG:-0} 2>&1 | grep -E "Traceback|Error" || true
prev=work/clips_o.glb
if [ -f scripts/arm_jobs.txt ]; then k=0
  while read -r clips cap sig; do
    [ -z "$clips" ] && continue; [[ "$clips" == \#* ]] && continue; k=$((k + 1))
    $G -W ignore scripts/arm_clear.py work/clips_o.glb work/cl_c$k.glb --side L=' L ' --side R=' R ' --clips $clips --outer-only --max-deg $cap --sigma 2.0 --root Pelvis 2>&1 | grep -E "Traceback|Error" || true
    FADE=0.16 $G -W ignore scripts/arm_soft.py $prev work/cl_c$k.glb work/cl_a$k.glb $cap $sig $clips 2>&1 | grep -E "Traceback|Error" || true
    prev=work/cl_a$k.glb
  done < scripts/arm_jobs.txt
fi
cp $prev work/clips_arm.glb
$G -W ignore scripts/half_keys.py work/clips_arm.glb work/half.glb 2>&1 | grep -E "Traceback|Error|HALF"
$G -W ignore scripts/half_keys.py work/clips_o.glb work/ref_half.glb 2>&1 | grep -E "Traceback|Error" || true
