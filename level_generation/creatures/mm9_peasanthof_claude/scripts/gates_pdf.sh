#!/usr/bin/env bash
# Gate run on one delivered design GLB (project folder): arm and hand gate, jitter vs the retargeted clips before the
# finger/hand-rest passes, detached parts, flat shading, texture quality, bone lengths, winding. Outputs review/gates/<d>/.
# Usage: scripts/gates_pdf.sh d1
set -u
d=$1; k=${d#d}
G=export/mm9_peasantdf$k.glb; O=review/gates/$d; mkdir -p $O
CAP="systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0"
$CAP python3 scripts/arm_hand_gate.py $G $O/arm_hand_gate.json --side "L= L " --side "R= R " --outer-only > $O/arm_hand_gate.txt 2>&1
$CAP python3 scripts/jitter_gate.py $G work/mm9_pdf${k}_clips.glb $O/jitter_gate.json --side "L= L " --side "R= R " > $O/jitter_gate.txt 2>&1
$CAP python3 ../claude_shared/detached_parts_audit.py $G > $O/detached.txt 2>&1
$CAP python3 ../claude_shared/flat_shading_check.py $G > $O/flat_shading.txt 2>&1
$CAP python3 ../claude_shared/texture_quality.py $G --json $O/texture_quality.json > $O/texture_quality.txt 2>&1
$CAP python3 ../claude_shared/bone_length_audit.py $G > $O/bones.txt 2>&1
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py $G > $O/winding.txt 2>&1
echo GATES DONE $d
