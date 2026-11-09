#!/bin/bash
# Meshy paints + head projections -> final images (project folder)
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
python3 scripts/compose_hw.py abc | tail -1
A="--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.03 --saturation 0.92"
$G ../claude_shared/grade_basecolor.py --ao textures/hw_torso_ao.png $A textures/hw_torso_a_raw.png textures/hw_torso_b_raw.png textures/hw_torso_c_raw.png 2>&1 | tail -1 | cut -c1-120
$G ../claude_shared/grade_basecolor.py --ao textures/hw_limbs_ao.png $A textures/hw_limbs_a_raw.png textures/hw_limbs_c_raw.png 2>&1 | tail -1 | cut -c1-120
python3 scripts/finish_tex.py
