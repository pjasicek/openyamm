#!/usr/bin/env bash
# All numeric gates on export/mm9_skeleton.glb, reports in review/. Project folder.
cd "$(dirname "$0")/.."; G=../claude_shared/gltf_venv/bin/python; R=review; X=export/mm9_skeleton.glb
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $X 2>&1 | grep -E 'INVERTED|WINDING' > $R/g_winding.txt
$G ../claude_shared/flat_shading_check.py $X 2>&1 | grep -v frozen | tail -2 > $R/g_flat.txt
$G ../claude_shared/texture_quality.py $X 2>&1 | grep -v frozen | tail -4 > $R/g_texture.txt
$G scripts/collapse_gate.py $X $R/collapse_body.json 0 2>&1 | grep -v frozen > $R/collapse_body.txt
$G scripts/collapse_gate.py $X $R/collapse_head.json 1 2>&1 | grep -v frozen > $R/collapse_head.txt
$G scripts/scrap_gate.py $X 1.1193 $R/scrap_gate.json > $R/scrap_gate.txt 2>&1
$G scripts/hand_bone_gate.py $X 1.1193 $R/hand_bone_gate.json > $R/hand_bone_gate.txt 2>&1
$G scripts/arm_hand_gate.py $X $R/arm_hand_gate.json --side L=' L ' --side R=' R ' --outer-only --exact > $R/arm_hand_gate.txt 2>&1
$G scripts/jitter_gate.py $X work/skel_clips_raw.glb $R/jitter_gate.json --side L=' L ' --side R=' R ' > $R/jitter_gate.txt 2>&1
cd ../../..
python3 tools/run_creature_review.py --project level_generation/creatures/mm9_skeleton_claude check > level_generation/creatures/mm9_skeleton_claude/review/g_viewer_check.txt 2>&1
echo final gates done > level_generation/creatures/mm9_skeleton_claude/review/g_done.txt
