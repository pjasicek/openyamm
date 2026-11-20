#!/bin/bash
# Numeric gates on one runtime GLB (installed or lined candidate): the creature's own arm/hand, jitter (vs its MM9-clip
# reference) and sleeve-poke gates (../mm9_tryggva_claude/scripts, read in place, options as the reduction's gates.sh), the
# shared audits, winding, the reduction UV audit against the installed file, additions-only identity and LOD floor/heights.
# Usage (any folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
P=/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_tryggva_lining_claude; cd $P
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_tryggva_claude/scripts
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
B=$P/before/mm9_tryggva.glb
$G $S/arm_hand_gate.py $glb $out/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_hand.txt 2>&1 &
$G $S/sleeve_poke_gate.py $glb $out/sleeve_poke.json > $out/sleeve_poke.txt 2>&1 &
wait
$G $S/jitter_gate.py $glb $C/mm9_tryggva_claude/work/mm9_try_clips.glb $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
$G $C/claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1 &
wait
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G $C/claude_shared/reduction_uv_audit.py $glb $B > $out/uv_audit.txt 2>&1
$G scripts/verify_identity.py $B $glb > $out/identity.txt 2>&1
$G scripts/lod_floor.py $glb > $out/lod_floor.txt 2>&1
echo GATESDONE > $out/done.txt
