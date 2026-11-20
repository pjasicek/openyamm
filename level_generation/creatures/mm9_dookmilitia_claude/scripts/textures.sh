#!/bin/bash
# Meshy paints + head projections -> final images (project folder). scripts/project_head.py abc first, once.
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
python3 scripts/compose_dook.py abc | tail -1
python3 scripts/compose_tier_b.py
A="--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.03 --saturation 0.8"
$G ../claude_shared/grade_basecolor.py --ao textures/dook_torso_ao.png $A textures/dook_torso_a_raw.png textures/dook_torso_b_raw.png textures/dook_torso_c_raw.png 2>&1 | tail -1 | cut -c1-120
$G ../claude_shared/grade_basecolor.py --ao textures/dook_limbs_ao.png $A textures/dook_limbs_a_raw.png textures/dook_limbs_c_raw.png 2>&1 | tail -1 | cut -c1-120
python3 scripts/tone_dook.py | cut -c1-90
python3 scripts/finish_tex.py
python3 scripts/tier_paint.py
# run 2: after this, scripts/project_strip.py apply abc repaints the cheek strip under the bars; it reads the head images it starts from in work/run2/tex_r12/ (delete that folder after a fresh project_head.py so it re-reads them)
