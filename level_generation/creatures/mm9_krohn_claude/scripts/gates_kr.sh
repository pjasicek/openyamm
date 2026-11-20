#!/usr/bin/env bash
# Gate run on the delivered GLB (project folder): jitter vs the untouched MM9 clips, sleeve poke, glaive and sword against
# the body, detached parts, flat shading, texture quality, bone lengths, winding. Outputs in review/$GD/ (default gates_r1).
# The arm and hand gate runs separately (scripts/arm_hand_gate.py ... --exclude-bones Xspear,Xspearmid,Xsword,Xswordbase).
set -u
G=export/mm9_kr.glb; O=review/${GD:-gates_r1}; mkdir -p $O
CAP=(systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0)
"${CAP[@]}" python3 scripts/jitter_gate.py $G work/mm9_kr_clips.glb $O/jitter_gate.json --side "L= L " --side "R= R " > $O/jitter_gate.txt 2>&1
"${CAP[@]}" python3 scripts/sleeve_poke_gate.py $G $O/sleeve_poke.json > $O/sleeve_poke.txt 2>&1
FPS=24 "${CAP[@]}" python3 scripts/prop_gate.py $G $O/spear_gate.json > $O/spear_gate.txt 2>&1
PROP=Xsword FPS=24 "${CAP[@]}" python3 scripts/prop_gate.py $G $O/sword_gate.json > $O/sword_gate.txt 2>&1
"${CAP[@]}" python3 ../claude_shared/detached_parts_audit.py $G > $O/detached.txt 2>&1
python3 ../claude_shared/flat_shading_check.py $G > $O/flat_shading.txt 2>&1
python3 ../claude_shared/texture_quality.py $G --json $O/texture_quality.json > $O/texture_quality.txt 2>&1
python3 ../claude_shared/bone_length_audit.py $G > $O/bones.txt 2>&1
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py $G > $O/winding.txt 2>&1
echo GATES DONE
