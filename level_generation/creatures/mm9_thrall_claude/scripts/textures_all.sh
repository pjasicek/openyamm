#!/bin/bash
# paints -> final images. TOKEN not needed. Project folder. AO bake (Blender): scripts/run.sh texpass_bake_ao.py <upload> textures/thrall_ao_4k.png 0.25 4096
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
$G scripts/compose_thrall.py 2>&1 | tail -1
for p in torso_a torso_b torso_c limbs_a limbs_b limbs_c; do pt=${p%_*}; $G ../claude_shared/grade_basecolor.py --ao textures/thrall_${pt}_ao.png --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.05 textures/thrall_${p}_raw.png 2>&1 | tail -1 | cut -c1-80; done
for f in textures/thrall_torso_a_normal textures/thrall_torso_b_normal textures/thrall_torso_c_normal textures/thrall_limbs_normal; do :; done
PYTHONPATH=scripts $G scripts/project_head.py abc 2048 2>&1 | grep -E 'HEAD|Trace|Error' | cut -c1-80
scripts/textures.sh
