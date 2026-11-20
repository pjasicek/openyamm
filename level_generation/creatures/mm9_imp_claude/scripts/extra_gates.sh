#!/usr/bin/env bash
# Gates on the dropped MM9 clips (run2-clips-groupD, 2026-10-31), new clips only; outputs in review/clips_restore_D/.
set -uo pipefail
cd "$(dirname "$0")/.."
G=../claude_shared/gltf_venv/bin/python; O=review/clips_restore_D; mkdir -p $O
C=Fidget2,Aware,Hit2,Death2,Dead2,Backpedal,BackpedalRun
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
Q $G ../claude_shared/new_clip_measure.py work/mm9_imp_grafted.glb $C --json $O/measure.json > $O/measure.txt
Q python3 ../claude_shared/bone_length_audit.py work/mm9_imp_grafted.glb > $O/bones.txt
Q $G scripts/arm_hand_gate.py work/mm9_imp_grafted.glb $O/arm_hand.json --side "L= L " --side "R= R " --outer-only --exact --clips $C > $O/arm_hand.txt
Q $G scripts/jitter_gate.py work/mm9_imp_grafted.glb work/extra_raw.glb $O/jitter.json --side "L= L " --side "R= R " --clips $C > $O/jitter.txt
Q $G scripts/blade_gate.py work/full_extra.glb $O/blade.json > $O/blade.txt
Q $G ../claude_shared/extra_clip_gates.py work/mm9_imp_grafted.glb --clips $C --ref-clips Standing,Walking,Hit,Death --out $O > $O/extra_gates.txt
echo DONE > $O/done.txt
