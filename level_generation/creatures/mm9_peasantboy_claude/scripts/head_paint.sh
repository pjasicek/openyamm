#!/usr/bin/env bash
# Head set paint chain (project folder): compose from the Meshy head returns (old head layout) -> carry into the new
# layout (relayout_head.py: the face one chart; transfer_head_paint.py bake + transfer_head_merge.py) -> flat head
# normals -> elf ear islands -> mouth plate -> face paint fixes -> gutter padding. Re-run as a whole.
# Needs work/face_v2.blend (master with HeadUV and HeadUV_old), work/mouth_uv.json (mouth_mask.py on face_v2) and
# work/head_texel_pos.npz (head_texel_pos.py on an export of face_v2) and work/head_texel_pos_old.npz (on an export of
# work/face_v1r.blend: the old layout's coverage, to pad the composed maps before the transfer).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
PYG=../claude_shared/gltf_venv/bin/python
for x in "pboy_tp:head_a_tp" "pboyb_tp:head_b_tp" "pboye_tp:head_e_tp"; do
  PYTHONPATH=/usr/lib/python3/dist-packages $PYG scripts/compose_headhand.py ${x%%:*} meshy/${x##*:} \
    textures/pboy_tp_basecolor_graded.png textures/pboy_tp_material_classes.png textures/pboy_tp_metal_rough_1k.png \
    --ref-head --ref-lum-min 150 --hand-gain 1.12 2>&1 | grep HEADHAND
done
HEADPOS=work/head_texel_pos_old.npz ORM=1 python3 scripts/pad_head_boy.py pboy_tp pboyb_tp pboye_tp
IMGS=""; for p in pboy_tp pboyb_tp pboye_tp; do IMGS="$IMGS $here/textures/${p}_head_basecolor.png $here/textures/${p}_head_metal_rough_1k.png"; done
(cd "$repo" && CREATURE_3D_TOKEN=$(cat "$here/LEASE_TOKEN.txt") tools/run_creature_blender.sh \
  level_generation/creatures/mm9_peasantboy_claude/scripts/transfer_head_paint.py "$here/work/face_v2.blend" $IMGS >/dev/null 2>&1)
python3 scripts/transfer_head_merge.py $IMGS
python3 scripts/head_normal_flat.py pboy_tp pboyb_tp pboye_tp
python3 scripts/elf_ear_paint.py pboy_tp pboyb_tp pboye_tp
# (fourth pass) mouth_paint.py dropped: mouth_close.py deleted the slit plate it painted
python3 scripts/face_paint_fix.py pboy_tp pboyb_tp pboye_tp
for p in pboy_tp pboyb_tp pboye_tp; do HAND_REF=$(cat work/hand_ref_$p.txt) python3 scripts/hand_clean.py $p | tail -1; done
python3 scripts/pad_head_boy.py pboy_tp pboyb_tp pboye_tp
