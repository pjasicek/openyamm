#!/usr/bin/env bash
# PeasantM5 copy of Markel's (sequential, memory-capped). All numeric gates on the current build (project folder): arm and hand, sleeve poke, jitter (vs MM9's untouched clips,
# unmirrored), bones, detached, flat shading, winding, texture quality. Outputs in review/<dir> (default gates).
set -uo pipefail
cd "$(dirname "$0")/.."
O=review/${1:-gates}; mkdir -p $O
G=../claude_shared/gltf_venv/bin/python
Q() { systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 env PYTHONPATH=/usr/lib/python3/dist-packages "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning\|frozen site" ; }
Q $G scripts/arm_hand_gate.py work/r16_final.glb $O/arm_hand.json --side "L= L " --side "R= R " > $O/arm_hand.txt
Q python3 scripts/sleeve_poke_gate.py work/r16_final.glb $O/sleeve_poke.json > $O/sleeve_poke.txt
Q $G scripts/jitter_gate.py work/mm9_pm5_unmirrored.glb work/mm9_pm5_clips.glb $O/jitter.json --side "L= L " --side "R= R " > $O/jitter.txt
Q python3 ../claude_shared/bone_length_audit.py work/r16_final.glb > $O/bones.txt
Q python3 ../claude_shared/detached_parts_audit.py work/r16_final.glb --json $O/detached.json > $O/detached.txt
Q python3 scripts/shading_check.py work/r16_final.glb > $O/shading.txt
Q python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py work/r16_final.glb > $O/winding.txt
Q python3 ../claude_shared/texture_quality.py work/r16_final.glb --json $O/texture_quality.json > $O/texture_quality.txt
echo DONE > $O/done.txt
