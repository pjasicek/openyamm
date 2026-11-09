#!/usr/bin/env bash
# Gate run on the delivered GLB (project folder; mm9_peasantdm1_claude's gates.sh + PeasantM7's sleeve-poke gate):
# arm and hand gate, jitter vs MM9's untouched clips, sleeve poke, detached parts, flat shading, texture quality, bone
# lengths, winding. Outputs in review/gates/.
set -u
G=export/mm9_pm7d.glb; O=review/gates; mkdir -p $O
python3 scripts/arm_hand_gate.py $G $O/arm_hand_gate.json --side "L= L " --side "R= R " --outer-only > $O/arm_hand_gate.txt 2>&1
python3 scripts/jitter_gate.py $G work/mm9_pm7d_clips.glb $O/jitter_gate.json --side "L= L " --side "R= R " > $O/jitter_gate.txt 2>&1
python3 scripts/sleeve_poke_gate.py $G $O/sleeve_poke.json > $O/sleeve_poke.txt 2>&1
python3 ../claude_shared/detached_parts_audit.py $G > $O/detached.txt 2>&1
python3 ../claude_shared/flat_shading_check.py $G > $O/flat_shading.txt 2>&1
python3 ../claude_shared/texture_quality.py $G --json $O/texture_quality.json > $O/texture_quality.txt 2>&1
python3 ../claude_shared/bone_length_audit.py $G > $O/bones.txt 2>&1
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py $G > $O/winding.txt 2>&1
echo GATES DONE
