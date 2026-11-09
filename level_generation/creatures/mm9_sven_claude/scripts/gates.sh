#!/usr/bin/env bash
# Gate run on the delivered GLB (project folder): arm and hand gate, jitter vs MM9's untouched clips, sleeve/bracer poke,
# detached parts, flat shading, texture quality, bone lengths, winding, numeric floor/stretch/wrist gates. review/gates/.
set -u
G=export/mm9_sven.glb; O=review/gates; V=../claude_shared/gltf_venv/bin/python
mkdir -p $O
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning"; }
Q $V scripts/arm_hand_gate.py $G $O/arm_hand_gate.json --side "L= L " --side "R= R " --outer-only > $O/arm_hand_gate.txt
Q $V scripts/jitter_gate.py $G work/mm9_sven_clips.glb $O/jitter_gate.json --side "L= L " --side "R= R " > $O/jitter_gate.txt
Q $V scripts/sleeve_poke_gate.py $G $O/sleeve_poke.json > $O/sleeve_poke.txt
Q $V ../claude_shared/detached_parts_audit.py $G > $O/detached.txt
Q $V ../claude_shared/flat_shading_check.py $G > $O/flat_shading.txt
Q $V ../claude_shared/texture_quality.py $G --json $O/texture_quality.json > $O/texture_quality.txt
Q $V ../claude_shared/bone_length_audit.py $G > $O/bones.txt
Q python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py $G > $O/winding.txt
Q $V scripts/gates.py $G $O/numeric.json Hand "Bip01 Head" "Bip01 L Toe0,Bip01 R Toe0" > $O/numeric.txt
echo GATES DONE
