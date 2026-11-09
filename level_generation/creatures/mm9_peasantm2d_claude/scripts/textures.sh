#!/bin/bash
# Meshy paint + head projection -> final images (project folder)
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
python3 scripts/compose_nj.py a | tail -1
A="--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.03 --saturation 0.92"
$G ../claude_shared/grade_basecolor.py --ao textures/nj_torso_ao.png $A textures/nj_torso_a_raw.png 2>&1 | tail -1 | cut -c1-120
$G ../claude_shared/grade_basecolor.py --ao textures/nj_limbs_ao.png $A textures/nj_limbs_a_raw.png 2>&1 | tail -1 | cut -c1-120
python3 scripts/tone_nj.py
python3 scripts/finish_tex.py
