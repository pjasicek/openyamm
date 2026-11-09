#!/usr/bin/env bash
# Rig + clips on a mesh npz (project folder): scripts/rig_sk.sh <mesh npz (asm or uv)> -> work/clips.glb
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
M=${1:-work/asm1.npz}; A=${ASM:-work/asm1.npz}
$G -W ignore scripts/fit_rig_sk.py $A source/mm9/skraelos.glb work/rig.json 2>&1 | grep -E "Traceback|Error|ARM|RIG" | cut -c1-160
$G -W ignore scripts/weights_sk.py $A work/mm9.npz work/rig.json work/weights.npz 2>&1 | grep -E "Traceback|Error|WEIGHTS|HOOD|mirror|SEAM"
$G -W ignore scripts/build_glb_sk.py $M work/weights.npz work/body.glb 2>&1 | grep -E "Traceback|Error|GLB"
$G -W ignore scripts/clips_pf.py work/body.glb work/clips.glb ${ROLES:-scripts/roles_sk.json} work/clips.json 2>&1 | grep -E "Traceback|Error|CLIPS|clip|role" | cut -c1-200
# arm corrections (Igrid's arm jobs: arm_clear.py solves the least upper-arm turn that clears the body, arm_soft.py blends it in smoothly)
prev=work/clips.glb
if [ -f scripts/arm_jobs_sk.txt ]; then k=0
  while read -r clips cap sig; do
    [ -z "$clips" ] && continue; [[ "$clips" == \#* ]] && continue; k=$((k + 1))
    $G -W ignore scripts/arm_clear.py work/clips.glb work/cl_c$k.glb --side L=' L ' --side R=' R ' --clips $clips --outer-only --max-deg $cap --sigma 2.0 --root 'FHP Pelvis' 2>&1 | grep -E "Traceback|Error" || true
    FADE=${ARMFADE:-0.3} $G -W ignore scripts/arm_soft.py $prev work/cl_c$k.glb work/cl_a$k.glb $cap $sig $clips 2>&1 | grep -E "Traceback|Error" || true
    prev=work/cl_a$k.glb
  done < scripts/arm_jobs_sk.txt
fi
if [ -f scripts/arm_clip_sk.txt ]; then $G -W ignore scripts/arm_out_clip.py $prev work/clips_ac.glb $(cat scripts/arm_clip_sk.txt) | tail -1; prev=work/clips_ac.glb; fi
cp $prev work/clips_arm_nostaff.glb
# the staff turned in the fist where it ran into the sleeve cuff / robe (staff_fix.py, on its own bone)
$G -W ignore scripts/staff_fix.py work/clips_arm_nostaff.glb work/clips_arm.glb ${STAFF_CLIPS:-Fidget,Talk,Running,Death,ResurrectSpell,Hit,Standing,Walking} 2>&1 | grep -E 'STAFF|Error|Trace'
