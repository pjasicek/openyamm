#!/bin/bash
# mm9_greenman paint chain (project folder). Body: the grade's output (work/gm_tp_basecolor_graded_orig.png) -> leaf_tone.py ->
# wrist_vine.py. Head: compose_headhand.py (hand gain) -> work/..._composed.png -> face_lines.py -> wrist_vine.py ->
# staff_paint.py. Rerunnable: every step starts from the saved source copies.
set -e
cd "$(dirname "$0")/.."
V=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
GLB=${GLB:-work/gm_body_tex.glb}
"$V" -W ignore scripts/compose_headhand.py gm_tp meshy/head_tp textures/gm_tp_basecolor_graded.png textures/gm_tp_material_classes.png textures/gm_tp_metal_rough_1k.png --ref-texels work/skin_ref.npy --hand-gain ${HANDGAIN:-1.12} 2>&1 | grep HEADHAND
cp textures/gm_tp_head_basecolor.png work/gm_tp_head_basecolor_composed.png
"$V" -W ignore scripts/leaf_tone.py "$GLB" 2>&1 | grep LEAFTONE
python3 scripts/face_lines.py textures/gm_tp_head_basecolor.png | cut -c1-120
python3 scripts/blue_specks.py textures/gm_tp_head_basecolor.png
"$V" -W ignore scripts/leaf_jitter.py "$GLB" textures/gm_tp_head_basecolor.png 2>&1 | grep LEAFJITTER
"$V" -W ignore scripts/wrist_vine.py "$GLB" textures/gm_tp_basecolor_graded.png textures/gm_tp_head_basecolor.png 2>&1 | grep WRISTVINE
python3 scripts/staff_paint.py gm_tp 0.33 2.5
# pass 2: toward MM9's darker olive and moss (last: the staff strip and the eyes are left out)
python3 scripts/colour_mm9.py textures/gm_tp_basecolor_graded.png textures/gm_tp_head_basecolor.png
