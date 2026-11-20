#!/bin/bash
# Tier C (HOF2, row 64) paint chain (project folder), fresh from the Meshy maps: body compose + gentle grade -> head/hands
# compose -> head_fix -> seam_tone -> face_paint. Positions from the HOF2 export (work/phof2_body_tex.glb); the HOF2 head sits
# DY/DZ off HOF1's in the export frame (fit_rig recentred the variant), passed to the position rules.
# Env: HAIR (head parts of hair: shell/fringe, never the kerchief), EARS, DY, DZ, CUT (seam height), EYES (x,y;x,y)
set -e
PY="systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 ../claude_shared/gltf_venv/bin/python"
G=${1:-work/phof2_body_tex.glb}
$PY scripts/compose_texpass.py phofc_tp meshy/body_retexture_c texturing/phof2_body_upload_tp.glb textures/phof2_tp_ao.png 2>&1 | grep COMPOSE
python3 ../claude_shared/grade_basecolor.py --ao textures/phof2_tp_ao.png --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 \
  --saturation 1.15 textures/phofc_tp_basecolor.png | tail -1
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 python3 scripts/compose_headhand.py phofc_tp meshy/head_retexture_c \
  textures/phofc_tp_basecolor_graded.png textures/phofc_tp_material_classes.png textures/phofc_tp_metal_rough_1k.png --ref-head --ref-lum-min 140 2>&1 | grep HEADHAND
RESET=1 $PY scripts/head_fix_phof.py $G phofc_tp phofc_tp --hair "${HAIR:-}" --ears "${EARS:-}" --dy ${DY:-0} --dz ${DZ:-0} 2>&1 | grep -E "HEADFIX|PALEFILL"
RESET=1 $PY scripts/seam_tone.py $G phofc_tp --cut ${CUT:-1.617} --body-mat PeasantHOF --head-mat PeasantHOFHead 2>&1 | grep SEAM
RESET=1 $PY scripts/face_paint_phof.py $G phofc_tp --eyes "${EYES}" --dy ${DY:-0} --dz ${DZ:-0} --sat 0.64 2>&1 | grep FACEPAINT
$PY scripts/hand_tone.py $G phofc_tp --dy ${DY:-0} --dz ${DZ:-0} 2>&1 | grep HANDTONE
# 2026-11-04 (coordinator pre-screen of r6): thin pale straight streaks the texpass drew across the dark dress islands, healed
RESET=1 python3 scripts/streak_heal.py textures/phofc_tp_basecolor_graded.png --dl 45 --dark 120 --votes 200 --run 40 | grep STREAKHEAL
# 2026-11-04: the pink band of ear paint on the kerchief beside each ear (and its dark speck) refilled from the cloth around it
RESET=1 $PY scripts/kerchief_smear_fix.py $G phofc_tp --dy ${DY:-0} --dz ${DZ:-0} 2>&1 | grep SMEARFIX
# 2026-11-04 (r9): ears toned to the skin beside them (in the body-tex frame the skin shell is part 1, the kerchief part 0)
RESET=1 $PY scripts/ear_tone.py work/phof2_body_tex.glb phofc_tp --ears 5,6 --skin 1 --gain 1.12 2>&1 | grep EARTONE
# 2026-11-04 (user review r7, r9): gutters re-padded last (head and body sets; colour, normal and ORM)
$PY scripts/pad_gutters.py work/phof2_body_tex.glb PeasantHOFHead textures/phofc_tp_head_basecolor.png 2>&1 | grep PADGUTTERS
$PY scripts/pad_gutters.py work/phof2_body_tex.glb PeasantHOF textures/phofc_tp_basecolor_graded.png 2>&1 | grep PADGUTTERS
for m in normal_1k metal_rough_1k; do $PY scripts/pad_gutters.py work/phof2_body_tex.glb PeasantHOFHead textures/phofc_tp_head_$m.png 2>&1 | grep PADGUTTERS
  $PY scripts/pad_gutters.py work/phof2_body_tex.glb PeasantHOF textures/phofc_tp_$m.png 2>&1 | grep PADGUTTERS; done
