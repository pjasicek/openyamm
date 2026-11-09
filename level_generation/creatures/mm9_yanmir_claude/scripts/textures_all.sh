#!/bin/bash
# paints -> final images (project folder). AO bake first: scripts/run.sh texpass_bake_ao.py <upload> textures/yan_ao_4k.png 0.3 4096
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
$G scripts/compose_yan.py 2>&1 | tail -1
$G ../claude_shared/grade_basecolor.py --ao textures/yan_body_ao.png --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.0 textures/yan_body_raw.png 2>&1 | tail -1 | cut -c1-100
$G scripts/tone_match.py textures/yan_body_raw_graded.png textures/yan_body_final.png 0.82 1.08
PYTHONPATH=scripts $G scripts/project_head.py a 2048 2>&1 | grep -E 'VIEWS|Trace|Error|MISSING' | cut -c1-160
cp textures/yan_head_a_raw.png textures/yan_head_final.png; cp textures/yan_head_a_normal.png textures/yan_head_normal.png
$G -c "
import numpy as np
from PIL import Image
Image.fromarray(np.dstack([np.full((64, 64), 255, 'u1'), np.full((64, 64), 175, 'u1'), np.zeros((64, 64), 'u1')])).save('textures/yan_head_orm.png')"
$G scripts/raster_pos.py 2048 | cut -c1-80
$G scripts/eyes.py textures/yan_head_final.png 2>&1 | tail -1
$G scripts/tone_match.py textures/yan_head_final.png textures/yan_head_final.png 0.92 1.05
rm -f textures/yan_body_preseam.png textures/yan_body_final_predisk.png textures/yan_body_orm_predisk.png textures/yan_head_final_prehair.png
$G scripts/hair_contrast.py
$G scripts/seam_blend.py
$G scripts/disks_silver.py
$G scripts/compose_acc.py
