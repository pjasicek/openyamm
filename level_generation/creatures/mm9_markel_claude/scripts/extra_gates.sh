#!/usr/bin/env bash
# Gates on the clips added for MM9's scripts (run2-clips-groupD, 2026-10-31), new clips only; outputs in v2/review/clips_restore_D/.
set -uo pipefail
cd "$(dirname "$0")/../.."
G=../claude_shared/gltf_venv/bin/python; O=v2/review/clips_restore_D; mkdir -p $O
C=Cower,Conv1,Conv3,Bow,PlayDeath,PlayGetUp
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
Q $G ../claude_shared/new_clip_measure.py v2/work/mm9_annud_grafted.glb $C --json $O/measure.json > $O/measure.txt
Q python3 ../claude_shared/bone_length_audit.py v2/work/mm9_annud_grafted.glb > $O/bones.txt
Q $G v2/scripts/arm_hand_gate.py v2/work/mm9_annud_grafted.glb $O/arm_hand.json --side "L= L " --side "R= R " --outer-only --exact --clips $C > $O/arm_hand.txt
Q $G v2/scripts/jitter_gate.py v2/work/mm9_annud_grafted.glb v2/work/extra_raw.glb $O/jitter.json --side "L= L " --side "R= R " --clips $C > $O/jitter.txt
Q $G ../claude_shared/extra_clip_gates.py v2/work/mm9_annud_grafted.glb --clips $C --ref-clips Standing,Walking,Talk,Death --out $O > $O/extra_gates.txt
echo DONE > $O/done.txt
