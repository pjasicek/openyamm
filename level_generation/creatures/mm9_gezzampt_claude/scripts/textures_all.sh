#!/bin/bash
# paints -> final images (project folder). AO bake first (Blender): scripts/run.sh texpass_bake_ao.py <upload> textures/gezz_ao_4k.png 0.3 4096
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
$G ../claude_shared/grade_basecolor.py --ao textures/gezz_body_ao.png --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.05 textures/gezz_body_raw.png 2>&1 | tail -1 | cut -c1-100
cp textures/gezz_body_raw_graded.png textures/gezz_body_final.png
PYTHONPATH=scripts $G scripts/project_head.py a 2048 2>&1 | grep -E 'VIEWS|HEAD|Trace|Error' | cut -c1-200
cp textures/gezz_head_a_raw.png textures/gezz_head_final.png; cp textures/gezz_head_a_normal.png textures/gezz_head_normal.png
$G scripts/eyes.py 2>&1 | tail -3 | cut -c1-120
$G - <<'P'
import numpy as np
from PIL import Image
Image.fromarray(np.dstack([np.full((64, 64), 255, 'u1'), np.full((64, 64), 190, 'u1'), np.zeros((64, 64), 'u1')])).save('textures/gezz_head_orm.png')
P
$G scripts/raster_pos.py 2048 | cut -c1-80
PYTHONPATH=scripts $G scripts/tier_ramps.py 2>&1 | grep -E 'RATIO|RAMPS|Trace|Error' | cut -c1-240
PYTHONPATH=scripts $G scripts/seam_fix.py 2>&1 | tail -1 | cut -c1-140
