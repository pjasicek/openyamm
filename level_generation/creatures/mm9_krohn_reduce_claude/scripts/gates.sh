#!/bin/bash
# Krohn's own numeric gates (../mm9_krohn_claude/scripts/gates_kr.sh + its arm/hand and see-through runs, README "Checks") on one
# runtime GLB (installed or candidate), run from the creature project folder (its scripts use relative ../claude_shared paths;
# outputs only go to this project's review/gates_<tag>/). Jitter against the creature's reference clips work/mm9_kr_clips.glb.
# Plus Yanmir's collapse gate (face collapse/flip per clip) and the clips/materials identity check.
# Usage (any folder): scripts/gates.sh <glb> <tag> [see]   (see: also the Blender see-through gate, 7 clips, step 5, 4.5 mm px)
set -u
cd "$(dirname "$0")/.."; HERE=$PWD
glb=$(realpath $1); out=$HERE/review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; K=$C/mm9_krohn_claude; S=$K/scripts
G="$HERE/scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"; P="$HERE/scripts/cap.sh python3"
cd $K
$G $C/mm9_yanmir_claude/scripts/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$P $S/jitter_gate.py $glb $K/work/mm9_kr_clips.glb $out/jitter_gate.json --side "L= L " --side "R= R " > $out/jitter_gate.txt 2>&1 &
$P $S/sleeve_poke_gate.py $glb $out/sleeve_poke.json > $out/sleeve_poke.txt 2>&1 &
wait
FPS=24 $P $S/prop_gate.py $glb $out/spear_gate.json > $out/spear_gate.txt 2>&1 &
PROP=Xsword FPS=24 $P $S/prop_gate.py $glb $out/sword_gate.json > $out/sword_gate.txt 2>&1 &
$P $S/arm_hand_gate.py $glb $out/arm_hand_gate.json --side "L= L " --side "R= R " --outer-only --exclude-bones Xspear,Xspearmid,Xsword,Xswordbase > $out/arm_hand_gate.txt 2>&1 &
wait
$P $C/claude_shared/detached_parts_audit.py $glb > $out/detached.txt 2>&1
python3 $C/claude_shared/flat_shading_check.py $glb > $out/flat_shading.txt 2>&1
python3 $C/claude_shared/texture_quality.py $glb --json $out/texture_quality.json > $out/texture_quality.txt 2>&1
python3 $C/claude_shared/bone_length_audit.py $glb > $out/bones.txt 2>&1
python3 $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G $HERE/scripts/same_clips.py $HERE/before/mm9_krohn.glb $glb > $out/same_clips.txt 2>&1
if [[ "${3:-}" == "see" ]]; then
  $HERE/scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1 --python $S/see_through_gate.py -- \
    $glb $out/see_through/see_through.json step=5 px_mm=4.5 clips=Standing,Walking,Running,Fidget,AttackMelee,Hit,Death > $out/see_through_full.txt 2>&1
  grep SEE_THROUGH $out/see_through_full.txt > $out/see_through.txt
fi
echo GATESDONE > $out/done.txt
