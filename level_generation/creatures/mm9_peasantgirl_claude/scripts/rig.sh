#!/usr/bin/env bash
# Rig + clips on a mesh npz (project folder): scripts/rig.sh <mesh npz (asm or uv)> -> work/half.glb (+ work/ref_half.glb, the same clips without arm corrections)
# DROP_PARTS=ears builds the human GLB (the elf ears left out); OUTSUF names the outputs (work/half$OUTSUF.glb)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
M=${1:-work/asm_frozen.npz}; S=${OUTSUF:-}
$G -W ignore scripts/fit_rig_pg.py work/asm_frozen.npz source/mm9/pg2/pg2.glb work/rig.json 2>&1 | grep -E "Traceback|Error|RIG" | cut -c1-160
$G -W ignore scripts/weights_pg.py work/asm_frozen.npz work/mm9.npz work/rig.json work/weights.npz 2>&1 | grep -E "Traceback|Error|WEIGHTS"
$G -W ignore scripts/build_glb_pg.py $M work/weights.npz work/body$S.glb 2>&1 | grep -E "Traceback|Error|GLB|DROPPED"
$G -W ignore scripts/clips_pf.py work/body$S.glb work/clips$S.glb ${ROLES:-scripts/roles_pg.json} work/clips$S.json 2>&1 | grep -E "Traceback|Error|CLIPS" | cut -c1-200
$G -W ignore scripts/${FINGERS:-finger_rest_pg.py} work/clips$S.glb work/clips_f$S.glb 2>&1 | grep -E "Traceback|Error|FINGER"
$G -W ignore scripts/pony_hang.py work/clips_f$S.glb work/clips_p$S.glb ${PONY_A0:-35} ${PONY_K:-0.3} 2>&1 | grep -E "Traceback|Error|PONY"
$G -W ignore scripts/pony_floor.py work/clips_p$S.glb work/clips_pf$S.glb 2>&1 | grep -E "Traceback|Error|PONY"
$G -W ignore scripts/skirt_gather.py work/clips_pf$S.glb work/clips_g$S.glb ${GATHER_K:-0.6} ${GATHER_FROM:-0.35} 2>&1 | grep -E "Traceback|Error|SKIRT"
$G -W ignore scripts/arm_out_pg.py work/clips_g$S.glb work/clips_o$S.glb R:${ARMDEG:-0} L:${ARMDEG:-0} 2>&1 | grep -E "Traceback|Error" || true
prev=work/clips_o$S.glb
if [ -f scripts/arm_jobs.txt ]; then k=0
  while read -r clips cap sig; do
    [ -z "$clips" ] && continue; [[ "$clips" == \#* ]] && continue; k=$((k + 1))
    $G -W ignore scripts/arm_clear.py work/clips_o$S.glb work/cl_c$k$S.glb --side L=' L ' --side R=' R ' --clips $clips --outer-only --max-deg $cap --sigma 2.0 --root Pelvis 2>&1 | grep -E "Traceback|Error" || true
    FADE=0.16 $G -W ignore scripts/arm_soft.py $prev work/cl_c$k$S.glb work/cl_a$k$S.glb $cap $sig $clips 2>&1 | grep -E "Traceback|Error" || true
    prev=work/cl_a$k$S.glb
  done < scripts/arm_jobs.txt
fi
cp $prev work/clips_arm$S.glb
$G -W ignore scripts/half_keys_pg.py work/clips_arm$S.glb work/half$S.glb 2>&1 | grep -E "Traceback|Error|HALF"
$G -W ignore scripts/half_keys_pg.py work/clips_o$S.glb work/ref_half$S.glb 2>&1 | grep -E "Traceback|Error" || true
