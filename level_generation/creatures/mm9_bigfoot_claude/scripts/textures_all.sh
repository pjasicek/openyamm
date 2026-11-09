#!/bin/bash
# paints -> final images (project folder). AO bake first: scripts/run.sh texpass_bake_ao.py <upload> textures/bf_ao_4k.png 0.3 4096
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
$G scripts/compose_bf.py 2>&1 | tail -1
$G ../claude_shared/grade_basecolor.py --ao textures/bf_body_ao.png --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.0 textures/bf_body_raw.png 2>&1 | tail -1 | cut -c1-100
cp textures/bf_body_raw_graded.png textures/bf_body_final.png
PYTHONPATH=scripts $G scripts/project_head.py ac 2048 2>&1 | grep -E 'VIEWS|Trace|Error|MISSING' | cut -c1-160
cp textures/bf_head_a_raw.png textures/bf_head_final.png; cp textures/bf_head_a_normal.png textures/bf_head_normal.png
$G - <<'P'
import numpy as np
from PIL import Image
Image.fromarray(np.dstack([np.full((64, 64), 255, 'u1'), np.full((64, 64), 190, 'u1'), np.zeros((64, 64), 'u1')])).save('textures/bf_head_orm.png')
Image.open('textures/bf_head_c_raw.png').convert('RGB').resize((1536, 1536), Image.LANCZOS).save('textures/bf_head_c_final.png')
P
$G scripts/raster_pos.py 2048 | cut -c1-80
$G scripts/eyes.py textures/bf_head_final.png 2>&1 | tail -1; $G scripts/eyes.py textures/bf_head_c_final.png 2>&1 | tail -1
PYTHONPATH=scripts $G scripts/tier_ramps.py 2>&1 | grep -E 'RAMPS|Trace|Error' | cut -c1-200
PYTHONPATH=scripts $G scripts/seam_fix.py 2>&1 | tail -1 | cut -c1-140
rm -rf work/neck_rim_in     # a full texture pass starts the rim from the fresh head set
PYTHONPATH=scripts $G scripts/neck_rim.py 2>&1 | grep -E "RIM|Trace|Error" | cut -c1-160      # run 2: the head rim takes the body grain and colour (reads its inputs from work/neck_rim_in/)
