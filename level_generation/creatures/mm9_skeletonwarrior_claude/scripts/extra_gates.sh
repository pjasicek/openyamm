#!/usr/bin/env bash
# Gates on the dropped MM9 clips (run2-clips-groupD, 2026-10-31), new clips only; outputs in review/clips_restore_D/.
set -uo pipefail
cd "$(dirname "$0")/.."
G=../claude_shared/gltf_venv/bin/python; O=review/clips_restore_D; mkdir -p $O
C=Search,AttackMeleeOld,AttackRangedOld,Hit2,Death2,Dead2,Backpedal,BackpedalRun
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
Q $G ../claude_shared/new_clip_measure.py work/mm9_skelwar_grafted.glb $C --json $O/measure.json > $O/measure.txt
Q python3 ../claude_shared/bone_length_audit.py work/mm9_skelwar_grafted.glb > $O/bones.txt
Q $G scripts/arm_hand_gate.py work/mm9_skelwar_grafted.glb $O/arm_hand.json --side "L= L " --side "R= R " --outer-only --exact --clips $C > $O/arm_hand.txt
# jitter reference: the same clips straight from clips_mm9.py (finger keys only), as the accepted gate used the raw MM9 keys
Q $G scripts/jitter_gate.py work/mm9_skelwar_grafted.glb work/extra_fingers.glb $O/jitter.json --side "L= L " --side "R= R " --clips $C > $O/jitter.txt
Q $G scripts/skirt_gate.py work/mm9_skelwar_grafted.glb $O/skirt.json $C > $O/skirt.txt
Q $G ../claude_shared/extra_clip_gates.py work/mm9_skelwar_grafted.glb --clips $C --ref-clips Standing,Walking,Hit,Death --out $O > $O/extra_gates.txt
echo DONE > $O/done.txt
