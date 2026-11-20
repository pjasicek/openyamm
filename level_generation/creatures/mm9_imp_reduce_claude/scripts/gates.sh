#!/bin/bash
# The Imp's own gates (../mm9_imp_claude README "Checks" and scripts/extra_gates.sh) on one runtime body GLB, plus
# same_clips.py against the installed file (imp-reduce-20261104): arm/hand (--outer-only --exact, 48 fps), jitter against MM9's
# raw clips (main clips: work/mm9_imp_clips.glb, dropped clips: work/extra_raw.glb), trident vs skin (blade_gate_split.py, the
# trident from its attachment GLB), stretch/floor/loop seams (gates.py), detached parts at 48 fps, flat shading, texture
# quality, bone lengths, winding. Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out; echo RUNNING > $out/done.txt
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; B=$C/mm9_imp_claude; S=$B/scripts
A=/home/pjasicek/github/OpenYAMM/assets_source/worlds/mm9/models
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
MAIN=Standing,Walking,Running,Fidget,Taunt,AttackMelee,AttackRanged,Hit,Death,Dead
EXTRA=Fidget2,Aware,Hit2,Death2,Dead2,Backpedal,BackpedalRun
$G $S/arm_hand_gate.py $glb $out/arm.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm.txt 2>&1 &
$G scripts/blade_gate_split.py $glb $A/mm9_imp_trident.glb $out/blade.json > $out/blade.txt 2>&1 &
wait
$G $S/jitter_gate.py $glb $B/work/mm9_imp_clips.glb $out/jitter.json --side L=' L ' --side R=' R ' --clips $MAIN > $out/jitter.txt 2>&1 &
$G $S/jitter_gate.py $glb $B/work/extra_raw.glb $out/jitter_extra.json --side L=' L ' --side R=' R ' --clips $EXTRA > $out/jitter_extra.txt 2>&1 &
wait
$G $S/gates.py $glb $out/stretch.json > $out/stretch.txt 2>&1
$G $C/claude_shared/detached_parts_audit.py $glb --fps 48 > $out/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_imp_reduce_claude/before/mm9_imp.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
