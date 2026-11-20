#!/bin/bash
# Fre head paint fixes on textures/pf_head_b_face.png (project folder; called by rebuild_fre.sh after sym_paint):
# under the jaw Meshy painted a dark-brown shadow (a goatee from below) -> throat skin (underchin_pf4.py, needs work/uv_tex2.npz);
# gutters between the head UV islands take their island edge's colour (thin dark seam lines on the cheek in the viewer).
set -e
python3 scripts/cap_hair_fre.py textures/pf_head_b_face.png textures/pf_head_b_face.png | tail -1
python3 scripts/hair_tone_fre.py textures/pf_head_b_face.png textures/pf_head_b_face.png | tail -1
python3 scripts/expose_skin_fre.py textures/pf_head_b_face.png textures/pf_head_b_face.png | tail -1
# pass 4: old-hood faces left between PeasantF2's hair rim and the face outline, and hair-like face texels beside the new hair -> skin
[ -n "$(python3 -c "import numpy as np; print('y' if 'hair2' in [str(x) for x in np.load('work/asm_frozen.npz')['names']] else '')")" ] && python3 scripts/seam_skin_fre.py textures/pf_head_b_face.png textures/pf_head_b_face.png | tail -1
# orchestrator r55: one smooth 3D-weighted heal of the bare temples/face sides from the clean cheek skin (no chart-shaped patches)
[ -f work/asm_frozen.npz ] && python3 scripts/temple_skin_fre.py base textures/pf_head_b_face.png textures/pf_head_b_face.png | tail -1
python3 scripts/skin_line_fre.py textures/pf_head_b_face.png textures/pf_head_b_face.png | tail -1
# pass 2: thin lines found in unlit nearest-texel renders (heal_lines_fre.py detect -> work/line_texels.npy, kept)
python3 scripts/heal_lines_fre.py apply textures/pf_head_b_face.png textures/pf_head_b_face.png | tail -1
python3 scripts/speck_heal_fre.py textures/pf_head_b_face.png textures/pf_head_b_face.png | tail -1
python3 scripts/gutter_fill_pf3.py work/uv_tex2.npz textures/pf_head_b_face.png | tail -1
python3 scripts/island_pad_fre.py 1 textures/pf_head_b_face.png textures/pf_head_b_face.png work/uv.npz head | tail -1
[ -n "${GUTTERFILL:-}" ] && python3 scripts/gutter_fill_pf3.py work/uv_tex2.npz textures/pf_head_normal.png | tail -1
python3 scripts/normal_line_fre.py textures/pf_head_normal.png textures/pf_head_normal.png | tail -1
python3 scripts/heal_lines_fre.py apply textures/pf_head_normal.png textures/pf_head_normal.png normal | tail -1
# pass 5: the hard-edged normal flattening of expose_skin/seam_skin drew lit panels at the temples (orchestrator r62); temple_skin's
# soft weight flattens the repainted area instead
[ -f work/temple_w.npz ] && python3 scripts/temple_skin_fre.py normal textures/pf_head_normal.png textures/pf_head_normal.png | tail -1
python3 scripts/island_pad_fre.py 1 textures/pf_head_normal.png textures/pf_head_normal.png work/uv.npz head | tail -1
