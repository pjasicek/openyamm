#!/bin/bash
# Tier B head chain (project folder; always from a fresh compose of the Meshy head): B's head set against the tier-B body (the shader-equivalent ramp preview of the
# shared body, a_tier_preview_body_phof1_b.png): head_fix (from the _preclean backups) -> seam_tone HEAD_ONLY (the head's
# neck band meets the B body) -> face_paint -> copy A's painted tusks. The phofb_tp / phofbx_tp body files are scratch.
set -e
PY="systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 ../claude_shared/gltf_venv/bin/python"
G=${1:-work/phof1_v9c_tex.glb}   # r10: texel positions of the mirrored-jaw geometry (was work/phofa_body_tex.glb)
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 python3 scripts/compose_headhand.py phofb_tp meshy/${HEADJOB_B:-head_retexture_b} \
  textures/phofa_tp_basecolor_graded.png textures/phofa_tp_material_classes.png textures/phofa_tp_metal_rough_1k.png --ref-head --ref-lum-min 140 2>&1 | grep HEADHAND
cp textures/a_tier_preview_body_phof1_b.png textures/phofb_tp_basecolor_graded.png
cp textures/a_tier_preview_body_phof1_b.png textures/phofbx_tp_basecolor_graded.png
cp textures/phofa_tp_normal_1k.png textures/phofb_tp_normal_1k.png
RESET=1 $PY scripts/head_fix_phof.py $G phofb_tp phofbx_tp --chin-half 0.035 2>&1 | grep -E "HEADFIX|PALEFILL"
RESET=1 HEAD_ONLY=1 $PY scripts/seam_tone.py $G phofb_tp --cut 1.632 --body-mat PeasantHOF --head-mat PeasantHOFHead 2>&1 | grep SEAM
RESET=1 $PY scripts/face_paint_phof.py $G phofb_tp 2>&1 | grep FACEPAINT
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 python3 scripts/compose_headhand.py phofaold_tp meshy/head_retexture_a textures/phofa_tp_basecolor_graded.png textures/phofa_tp_material_classes.png textures/phofa_tp_metal_rough_1k.png --ref-head --ref-lum-min 140 2>&1 | grep -c HEADHAND > /dev/null
if [[ "${COPY_TUSKS:-1}" == 1 ]]; then $PY scripts/copy_tusks.py $G phofaold_tp phofb_tp 2>&1 | grep COPY; fi
RESET=1 $PY scripts/hair_color.py $G phofb_tp --sat 0.92 --gain 1.22 --hue-pull 0.3 --side-x 9 2>&1 | grep HAIRCOLOR
# 2026-11-04 (fresh B2 paint read pale/grey against MM9's ruddy older woman): warmer skin + soft cheek flush; head only
# (the body prefix here is the scratch phofbx_tp)
RESET=1 $PY scripts/skin_warm.py $G phofb_tp phofbx_tp textures/a_region_mask.png --gain 1.02,0.94,0.86 --flush 0.18 2>&1 | grep SKINWARM
# 2026-11-04: the head shell's lowest strip (neck sides, nape) toned to tier B's body neck skin (jagged orange polygons)
RESET=1 $PY scripts/neck_even.py $G phofb_tp --preview textures/a_tier_preview_body_phof1_b.png --y-front 1.675 --y-back 1.70 --ramp 0.025 2>&1 | grep NECKEVEN
# 2026-11-04: ears toned to the cheek, skin seams outside the central face, cheek sides beside the braids 10 % darker
RESET=1 $PY scripts/ear_tone.py $G phofb_tp --gain 1.12 2>&1 | grep EARTONE   # r9: ears = the skin beside them
RESET=1 $PY scripts/skin_seam_blend.py $G phofb_tp --sidek 0.9 2>&1 | grep SKINSEAM
# 2026-11-04 (user review r7): hair-edge strip toned to the hair; gutters re-padded last
RESET=1 $PY scripts/fringe_edge.py $G phofb_tp 2>&1 | grep FRINGEEDGE
# r10 (2026-11-04): fresh b3 paint on the mirrored lower face; chin speck healed; her right cheek side toned to the mirror
# image of her left (pale side panel), the outermost cheek strip beside both ears flattened (pale vertical band)
python3 scripts/chin_speck.py textures/phofb_tp_head_basecolor.png | grep CHINSPECK
RESET=1 $PY scripts/cheek_line_heal.py $G phofb_tp --sigma 0.004 --xlo 0.05 --flatlo 0.066 --flathi 0.095 --fsig 0.01 --fdet 0.0012 2>&1 | grep -E "CHEEK"
$PY scripts/pad_gutters.py $G PeasantHOFHead textures/phofb_tp_head_basecolor.png 2>&1 | grep PADGUTTERS
# r9 (2026-11-04): normal and ORM gutters re-padded too (a viewer-only seam line)
$PY scripts/pad_gutters.py $G PeasantHOFHead textures/phofb_tp_head_normal_1k.png 2>&1 | grep PADGUTTERS
$PY scripts/pad_gutters.py $G PeasantHOFHead textures/phofb_tp_head_metal_rough_1k.png 2>&1 | grep PADGUTTERS
