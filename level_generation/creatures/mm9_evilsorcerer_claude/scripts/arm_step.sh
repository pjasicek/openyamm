#!/bin/bash
# arm correction only (for tuning), clips -> arm -> half. env ARMCAP ARMSIG ARMFADE. Writes work/arm2.txt, work/jitter2.txt
G=../claude_shared/gltf_venv/bin/python
AC="Fidget2,AttackRanged,AttackRanged2,ResurrectSpell,Death"
$G -W ignore scripts/arm_out.py work/clips.glb work/clips_o.glb R:7 2>&1 | grep -E "Traceback|Error"
$G -W ignore scripts/half_keys.py work/clips_o.glb work/ref_half.glb 2>&1 | grep -E "Traceback|Error"
$G -W ignore scripts/arm_clear.py work/clips_o.glb work/clips_clear.glb --side L=' L ' --side R=' R ' --clips $AC --outer-only --max-deg ${ARMCAP:-22} --sigma 2.0 2>&1 | grep -E "ARMCLEAR" | cut -c1-170 > work/clear.txt
FADE=${ARMFADE:-0.16} $G -W ignore scripts/arm_soft.py work/clips_o.glb work/clips_clear.glb work/clips_arm.glb ${ARMCAP:-22} ${ARMSIG:-0.09} $AC 2>&1 | grep -E "peak|Traceback|Error" | cut -c1-100
$G -W ignore scripts/half_keys.py work/clips_arm.glb work/half_t.glb 2>&1 | grep -E "Traceback|Error"
$G -W ignore scripts/arm_hand_gate.py work/half_t.glb work/arm2.json --side L=' L ' --side R=' R ' --outer-only --clips $AC 2>&1 | grep -v CHAINS | cut -c1-170 > work/arm2.txt
$G -W ignore scripts/jitter_gate.py work/half_t.glb work/ref_half.glb work/jitter2.json --side L=" L " --side R=" R " --clips $AC 2>&1 | grep -E "FAIL|JITTER" | cut -c1-300 > work/jitter2.txt
echo DONE > work/arm_step.done
