#!/bin/bash
# One gate run + sheets (project folder).
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python; g=work/trell_final_clips.glb; x=export/mm9_trellborg.glb; O=review/gates; R=/home/pjasicek/github/OpenYAMM
mkdir -p $O review/shots
$G scripts/collapse_gate.py $g $O/collapse.json > $O/collapse.txt 2>/dev/null &
$G scripts/jitter_gate.py $g work/trell_clips0c.glb $O/jitter.json --side L=' L ' --side R=' R ' > $O/jitter.txt 2>/dev/null &
wait
NOCLOTH=1 $G scripts/arm_hand_gate.py $g $O/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > $O/arm_hand.txt 2>/dev/null
$G scripts/club_gate.py $g > $O/club.txt 2>/dev/null
$G scripts/orient_gate.py $x source/true/trellborg1_true.glb $O/orient.json > $O/orient.txt 2>/dev/null
$G scripts/handedness.py source/t1/trellborg1.glb source/true/trellborg1_true.glb $x > $O/handedness.txt 2>/dev/null
$G ../claude_shared/detached_parts_audit.py $x --fps 24 > $O/detached.txt 2>/dev/null
$G ../claude_shared/flat_shading_check.py $x > $O/flat.txt 2>/dev/null
$G ../claude_shared/texture_quality.py $x > $O/texture_quality.txt 2>/dev/null
cd $R; python3 level_generation/creatures/claude_shared/floor/floor_audit.py --world mm9 --match 'MM9 Trellborg*' > level_generation/creatures/mm9_trellborg_claude/$O/floor.txt 2>&1
python3 tools/run_creature_review.py --project level_generation/creatures/mm9_trellborg_claude check > level_generation/creatures/mm9_trellborg_claude/$O/viewer_check.txt 2>&1
python3 level_generation/projects/mm9r_common/review_root.py > /dev/null 2>&1
./build/game/openyamm --world mm9 --headless-run-regression-suite actors --help >/dev/null 2>&1
echo GATES_DONE
