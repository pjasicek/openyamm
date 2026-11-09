#!/bin/bash
# paints -> final images (project folder). AO bake first: scripts/run.sh texpass_bake_ao.py <upload> textures/cw_ao_4k.png 0.3 4096
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
$G scripts/compose_cw.py 2>&1 | tail -1
$G ../claude_shared/grade_basecolor.py --ao textures/cw_body_ao.png --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.0 textures/cw_body_raw.png 2>&1 | tail -1 | cut -c1-100
cp textures/cw_body_raw_graded.png textures/cw_body_final.png
PYTHONPATH=scripts $G scripts/project_head.py b 2048 2>&1 | grep -E 'VIEWS|Trace|Error|MISSING' | cut -c1-160
cp textures/cw_head_b_raw.png textures/cw_head_final.png; cp textures/cw_head_b_normal.png textures/cw_head_normal.png
$G - <<'P'
import numpy as np
from PIL import Image
Image.fromarray(np.dstack([np.full((64, 64), 255, 'u1'), np.full((64, 64), 95, 'u1'), np.zeros((64, 64), 'u1')])).save('textures/cw_head_orm.png')   # wet slime: roughness 0.37
P
$G scripts/raster_pos.py 2048 | cut -c1-80
PYTHONPATH=scripts $G scripts/tier_ramps_cw.py 2>&1 | grep -E 'RAMPS|EYES|Trace|Error' | cut -c1-200
PYTHONPATH=scripts $G scripts/neck_rim_cw.py 2>&1 | grep -E "RIM|Trace|Error" | cut -c1-160
