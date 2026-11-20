#!/bin/bash
# Hag numeric gates on the runtime GLB into v2/review/gates/ (project folder). Blender gates through the lease wrapper.
cd "$(dirname "$0")/.."; R=/home/pjasicek/github/OpenYAMM; G=../claude_shared/gltf_venv/bin/python; g=v2/export/mm9_hag.glb; O=v2/review/gates; mkdir -p $O
T=$(awk '{print $2}' LEASE_TOKEN.txt)
$G -W ignore v2/scripts/arm_hand_gate.py $g $O/arm_hand.json --side L=" L " --side R=" R " --outer-only --exact 2>&1 | grep -v Unexpected > $O/arm_hand.txt &
$G -W ignore v2/scripts/jitter_gate.py $g v2/work/mm9_hag_clips.glb $O/jitter.json --side L=' L ' --side R=' R ' 2>&1 | grep -v Unexpected > $O/jitter.txt &
wait
$G -W ignore ../claude_shared/flat_shading_check.py $g 2>&1 | grep -v Unexpected | tail -6 > $O/flat.txt
$G -W ignore ../claude_shared/detached_parts_audit.py $g --fps 48 2>&1 | grep -v Unexpected | tail -30 > $O/detached.txt
$G -W ignore ../claude_shared/texture_quality.py $g 2>&1 | grep -v Unexpected | tail -40 > $O/texture_quality.txt
(cd $R && tools/run_creature_blender.sh --token $T level_generation/creatures/mm9_hag_claude/v2/scripts/sleeve_gate.py $R/level_generation/creatures/mm9_hag_claude/$g $R/level_generation/creatures/mm9_hag_claude/$O/sleeve_gate.json FHP > /dev/null 2>&1)
(cd $R && tools/run_creature_blender.sh --token $T level_generation/creatures/mm9_hag_claude/scripts/see_through_gate.py $R/level_generation/creatures/mm9_hag_claude/$g $R/level_generation/creatures/mm9_hag_claude/$O/see_through.json > $R/level_generation/creatures/mm9_hag_claude/$O/see_through.log 2>&1)
echo DONE
