#!/bin/bash
# all numeric gates on the runtime GLB (project folder). Writes review/gates/*.
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_zombie_claude; mkdir -p review/gates
G=$PWD/../claude_shared/gltf_venv/bin/python; g=export/mm9_zombie.glb
python3 scripts/collapse_gate.py $g review/gates/collapse.json > review/gates/collapse.txt 2>&1 &
python3 scripts/arm_hand_gate.py $g review/gates/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > review/gates/arm_hand.txt 2>&1 &
python3 scripts/jitter_gate.py $g work/zombie_clips_raw.glb review/gates/jitter.json --side L=' L ' --side R=' R ' > review/gates/jitter.txt 2>&1 &
python3 scripts/cloth_gate.py $g work/faces3.npz review/gates/cloth.json > review/gates/cloth.txt 2>&1 &
python3 ../claude_shared/detached_parts_audit.py $g --fps 24 > review/gates/detached.txt 2>&1 &
python3 ../claude_shared/flat_shading_check.py $g > review/gates/flat.txt 2>&1 &
wait
python3 ../claude_shared/texture_quality.py export/mm9_zombie.glb > review/gates/texture_quality.txt 2>&1
tail -3 review/gates/flat.txt | cut -c1-160; tail -2 review/gates/detached.txt | cut -c1-200; cat review/gates/cloth.txt | cut -c1-120; tail -2 review/gates/jitter.txt | cut -c1-200
