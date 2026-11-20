#!/bin/bash
# Meshy paints + head projection -> final images (project folder). AO first: scripts/run.sh texpass_bake_ao.py <upload> textures/trell_ao_4k.png 0.3 4096
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
python3 scripts/compose_trell.py abc | tail -1
$G ../claude_shared/grade_basecolor.py --ao textures/trell_body_ao.png --fine ${FINE:-0.7} --local 0.25 --ao-strength 0.55 --contrast 1.04 --saturation ${SAT:-0.92} textures/trell_body_a_raw.png textures/trell_body_b_raw.png textures/trell_body_c_raw.png 2>&1 | tail -1 | cut -c1-100
python3 scripts/tone_trell.py
PYTHONPATH=scripts $G scripts/project_head.py a 2048 2>&1 | grep -E 'VIEWS|HEAD|Trace|Error' | cut -c1-220
cp textures/trell_head_a_normal.png textures/trell_head_normal.png
$G - <<'P' 2>/dev/null
import numpy as np
from PIL import Image
Image.fromarray(np.dstack([np.full((64, 64), 255, 'u1'), np.full((64, 64), 190, 'u1'), np.zeros((64, 64), 'u1')])).save('textures/trell_head_orm.png')
P
$G scripts/raster_pos.py 2048 | cut -c1-80
$G scripts/tier_head.py 1536 2>&1 | grep -E 'TIERHAIR|MASKS|SKIN|HEADTIERS|Trace|Error' | cut -c1-220
