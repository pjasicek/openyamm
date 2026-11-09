#!/bin/bash
# Meshy paints + head projections -> final images (project folder)
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
python3 scripts/compose_clan.py abc | tail -1
A="--fine 0.7 --local 0.25 --ao-strength 0.6 --contrast 1.03 --saturation 1.0"
$G ../claude_shared/grade_basecolor.py --ao textures/clan_torso_ao.png $A textures/clan_torso_a_raw.png textures/clan_torso_b_raw.png textures/clan_torso_c_raw.png 2>&1 | tail -1 | cut -c1-120
$G ../claude_shared/grade_basecolor.py --ao textures/clan_limbs_ao.png $A --saturation 0.84 textures/clan_limbs_a_raw.png textures/clan_limbs_c_raw.png 2>&1 | tail -1 | cut -c1-120
python3 scripts/tone_clan.py 0.26 0.5 textures/clan_torso_a_raw_graded.png textures/clan_torso_b_raw_graded.png textures/clan_torso_c_raw_graded.png textures/clan_limbs_a_raw_graded.png textures/clan_limbs_c_raw_graded.png | tail -2
python3 scripts/finish_tex.py
