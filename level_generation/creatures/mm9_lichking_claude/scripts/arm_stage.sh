#!/usr/bin/env bash
# Arm corrections (after the coat keys: the hands clear the coat too), group by group: arm_clear.py then arm_soft.py (widened, capped, faded at
# the clip ends, applied on the raw keys). Usage: scripts/arm_stage.sh <in glb> <out glb>
set -euo pipefail
G=../claude_shared/gltf_venv/bin/python; prev=$1; k=0
while read -r clips cap sig loop; do
  k=$((k + 1))
  "$G" -W ignore scripts/arm_clear.py $1 work/cl_c$k.glb --side L=' L ' --side R=' R ' --clips $clips --outer-only --max-deg $cap --sigma 2.0 2>&1 | grep -E "Traceback|Error" || true
  LOOP=${loop:-0} FADE=0.16 "$G" -W ignore scripts/arm_soft.py $prev work/cl_c$k.glb work/cl_a$k.glb $cap $sig $clips 2>&1 | grep -E "Traceback|Error" || true
  prev=work/cl_a$k.glb
done <<'G_'
Standing,Walking,Backpedal,BackpedalRun 18 0.09 1
Fidget,Aware,Hit,Hit2,Fidget2,Search 18 0.09 0
Resurrect,Death,Death2,Death3 25 0.11 0
G_
cp $prev $2
