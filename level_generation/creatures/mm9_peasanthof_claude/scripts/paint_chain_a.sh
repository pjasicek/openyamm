#!/bin/bash
# Tier A paint chain (project folder), fresh from the Meshy maps: body compose + gentle grade -> head/hands compose ->
# head_fix -> seam_tone (body and head meet) -> face_paint. Then scripts/head_chain_b.sh for tier B's head.
set -e
PY="systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 ../claude_shared/gltf_venv/bin/python"
G=${1:-work/phof1_v9c_tex.glb}   # r10: texel positions of the mirrored-jaw geometry (was work/phofa_body_tex.glb)
$PY scripts/compose_texpass.py phofa_tp meshy/body_retexture_a texturing/phof_body_upload_tp.glb textures/phof_tp_ao.png 2>&1 | grep COMPOSE
python3 ../claude_shared/grade_basecolor.py --ao textures/phof_tp_ao.png --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 \
  --saturation 1.15 textures/phofa_tp_basecolor.png | tail -1
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 python3 scripts/compose_headhand.py phofa_tp meshy/head_retexture_${HEADJOB:-a2} \
  textures/phofa_tp_basecolor_graded.png textures/phofa_tp_material_classes.png textures/phofa_tp_metal_rough_1k.png --ref-head --ref-lum-min 140 2>&1 | grep HEADHAND
RESET=1 $PY scripts/head_fix_phof.py $G phofa_tp phofa_tp --chin-half 0.035 2>&1 | grep -E "HEADFIX|PALEFILL"
RESET=1 $PY scripts/hair_color.py $G phofa_tp --sat 1.0 --gain 1.05 --hue-pull 0.15 --detail 1.4 --side-x 9 2>&1 | grep HAIRCOLOR
$PY scripts/tiers_phof.py a $G 2>&1 | grep -c TIERS > /dev/null
RESET=1 $PY scripts/skin_warm.py $G phofa_tp phofa_tp textures/a_region_mask.png --body-auto 2>&1 | grep SKINWARM
RESET=1 $PY scripts/seam_tone.py $G phofa_tp --cut 1.632 --body-mat PeasantHOF --head-mat PeasantHOFHead 2>&1 | grep SEAM
RESET=1 $PY scripts/face_paint_phof.py $G phofa_tp 2>&1 | grep FACEPAINT
# 2026-11-04: the head shell's lowest strip (neck sides, nape) toned to tier A's body neck skin (jagged orange polygons)
RESET=1 $PY scripts/neck_even.py $G phofa_tp --preview textures/a_tier_preview_body_phof1_a.png --y-front 1.675 --y-back 1.70 --ramp 0.025 2>&1 | grep NECKEVEN
# coordinator review r2 (2026-11-02): fresh head paint a2 (warm ruddy skin, gentle smile, copper strands); light strand
# contrast and matte hair; the body skin region matched to the new head's neck tone
# 2026-11-04 (coordinator pre-screen of r6): ears toned to the cheek hue and darker (thin ears render pale); skin tone made continuous
# across the paint's projection seams outside the central face, the cheek sides beside the braids darkened 10 %;
# (r8: no jaw darkening; the pale wedge beside the jaw is two head-shell faces deleted in master_v8b, strip_delete.py)
RESET=1 $PY scripts/ear_tone.py $G phofa_tp --gain 1.12 2>&1 | grep EARTONE   # r9: ears = the skin beside them
RESET=1 $PY scripts/skin_seam_blend.py $G phofa_tp --sidek 0.9 2>&1 | grep SKINSEAM
# (gutter_faces_fix.py was tried for the jaw wedge: it is head shell, see skin_seam_blend --jawz)
# 2026-11-04 (user review r7): the skin under the hair shell's lower edge toned to the hair (pale strip along the top of the fringe);
# gutters re-padded last (the paint steps above left old padding at the UV seams: light lines down the cheek and chin)
RESET=1 $PY scripts/fringe_edge.py $G phofa_tp 2>&1 | grep FRINGEEDGE
# r10 (2026-11-04): fresh a3 paint on the mirrored lower face; a tusk-pale speck on the chin island's edge healed
python3 scripts/chin_speck.py textures/phofa_tp_head_basecolor.png | grep CHINSPECK
$PY scripts/pad_gutters.py $G PeasantHOFHead textures/phofa_tp_head_basecolor.png 2>&1 | grep PADGUTTERS
# r9 (2026-11-04): normal and ORM gutters re-padded too (a viewer-only seam line)
$PY scripts/pad_gutters.py $G PeasantHOFHead textures/phofa_tp_head_normal_1k.png 2>&1 | grep PADGUTTERS
$PY scripts/pad_gutters.py $G PeasantHOFHead textures/phofa_tp_head_metal_rough_1k.png 2>&1 | grep PADGUTTERS
