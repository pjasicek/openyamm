#!/bin/bash
# Meshy paint + head projection -> final images (project folder)
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
python3 scripts/compose_dwarf.py a | tail -1
A="--fine 0.7 --local 0.25 --ao-strength 0.6 --contrast 1.0 --saturation ${SAT:-0.84}"
$G ../claude_shared/grade_basecolor.py --ao textures/dwarf_torso_ao.png $A textures/dwarf_torso_a_raw.png 2>&1 | tail -1 | cut -c1-120
$G ../claude_shared/grade_basecolor.py --ao textures/dwarf_limbs_ao.png $A textures/dwarf_limbs_a_raw.png 2>&1 | tail -1 | cut -c1-120
python3 scripts/tone_dwarf.py ${TK:-0.3} ${TS:-0.6} textures/dwarf_torso_a_raw_graded.png textures/dwarf_limbs_a_raw_graded.png | tail -2
python3 scripts/finish_tex.py
