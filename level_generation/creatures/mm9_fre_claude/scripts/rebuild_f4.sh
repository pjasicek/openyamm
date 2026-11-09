#!/bin/bash
# PF4 rebuild from the paid inputs (project folder), under the 12G cap from the caller (systemd-run): head paint (sym -> fix -> hood tone per
# tier -> Codex faces aligned, nose fitted, projected) -> finish -> tiers -> finish -> tweak -> chin -> rig (F1 weights + PF4 parts) ->
# runtime -> viewer. Usage: scripts/rebuild_f4.sh <viewer rev> [--install]
# Never regenerated here: work/asm_frozen.npz (add_parts_pf4.py + fix_shards_pf4.py), work/uv.npz (uv_pf4.py: the paid layout),
# textures/pf_*_raw|normal|rough (compose_pf.py), the AO bakes, references_face/out_face_*.png (Codex).
set -e
python3 scripts/body_plain_pf4.py textures/pf_body_raw_meshy.png textures/pf_body_raw.png
# r29: the recoloured islands' gutters kept the old lacing colours (tiny lacing islands drew dark chevrons through bilinear filtering)
for f in pf_body_raw pf_body_normal_plain pf_ao_2k_plain; do python3 scripts/pad_set_pf4.py 0 textures/$f.png textures/$f.png > /dev/null; done
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages; FD=${FD:-references_face/v2}
python3 scripts/finish_pf.py > /dev/null
python3 scripts/tweak_pf1.py work/asm_frozen.npz work/uv_tex.npz work/uv_tex2_tw.npz 0.012 8 > /dev/null
python3 scripts/chin_pf4.py work/uv_tex2_tw.npz work/uv_tex2_chin.npz 16 0.005 | tail -1
python3 scripts/under_hood_pf4.py work/uv_tex2_chin.npz work/uv_tex2_uh.npz work/asm_frozen.npz | tail -1
python3 scripts/puff_pf4.py work/uv_tex2_uh.npz work/uv_tex2_puff.npz work/rig.json ${PUFFKEEP:-0.0}
python3 scripts/bust_pf4.py work/uv_tex2_puff.npz work/uv_tex2_bust.npz
python3 scripts/eyelid_pf4.py work/uv_tex2_bust.npz work/uv_tex2.npz
$G -W ignore scripts/sym_paint.py work/uv.npz 1 textures/pf_head_raw.png textures/pf_head_a_sym.png > /dev/null
$G -W ignore scripts/head_fix_pf4.py textures/pf_head_a_sym.png textures/pf_head_a_fix.png > /dev/null
python3 scripts/hood_tone_pf4.py textures/pf_head_a_fix.png textures/pf_head_a_hood.png | tail -1
python3 scripts/hood_tone_pf4.py textures/pf_head_a_fix.png textures/pf_head_b_hood.png ${HOODB:-0.93,0.84,0.76} | tail -1
for t in a b; do
  O=$FD/out_face_$t.png; [ -f $FD/out_face_${t}_tex.png ] && O=$FD/out_face_${t}_tex.png
  NOGAIN=$([ "$FD" = references_face ] || echo 1) python3 scripts/align_face_pf4.py $FD/in_face_$t.png $O $FD/out_face_${t}_aligned.png > /dev/null
  # v2 repaints a render of the projected face (its nose already sits on the geometry): no nose warp
  if [ "$FD" = references_face ]; then python3 scripts/warp_nose_pf1.py $FD/out_face_${t}_aligned.png $FD/out_face_${t}_nose.png > /dev/null; else cp $FD/out_face_${t}_aligned.png $FD/out_face_${t}_nose.png; fi
  NOSEKEEP=$([ "$FD" = references_face ] || echo 1) HAIRWIN=1 $G -W ignore scripts/project_face_pf4.py $t $FD/out_face_${t}_nose.png textures/pf_head_${t}_hood.png textures/pf_head_${t}_face.png 2>&1 | grep -E "PROJECT|Error|Trace" || true
  [ -n "${F1ZONES:-}" ] && python3 scripts/f1_lids_nose_pf4.py ../mm9_peasantf1_claude/textures/pf_head_b_face.png textures/pf_head_${t}_face.png textures/pf_head_${t}_face.png $F1ZONES
  python3 scripts/underchin_pf4.py textures/pf_head_${t}_face.png textures/pf_head_${t}_face.png
  python3 scripts/eyeball_lids_pf4.py textures/pf_head_${t}_face.png textures/pf_head_${t}_face.png ${LIDUP:-0.42} ${LIDLO:--0.55} | tail -1
  TAN=${TAN:-0.94,0.88,0.83} BLUSH=${BLUSH:-0.55} python3 scripts/skin_match_pf4.py head textures/pf_head_${t}_face.png textures/pf_head_${t}_face.png
  python3 scripts/pad_set_pf4.py 1 textures/pf_head_${t}_face.png textures/pf_head_${t}_face.png
done
cp textures/pf_head_b_face.png textures/pf_head_b_final.png
python3 scripts/finish_pf.py > /dev/null
$G -W ignore scripts/tiers_pf4.py 2>&1 | grep -E "grime|Error|Trace" || true
BODYFROMHEAD=1 python3 scripts/skin_match_pf4.py body textures/pf_body_tone.png textures/pf_body_tone.png
python3 scripts/finish_pf.py > /dev/null
python3 scripts/tweak_pf1.py work/asm_frozen.npz work/uv_tex.npz work/uv_tex2_tw.npz 0.012 8 > /dev/null
python3 scripts/chin_pf4.py work/uv_tex2_tw.npz work/uv_tex2_chin.npz 16 0.005 > /dev/null
python3 scripts/under_hood_pf4.py work/uv_tex2_chin.npz work/uv_tex2_uh.npz work/asm_frozen.npz > /dev/null
python3 scripts/puff_pf4.py work/uv_tex2_uh.npz work/uv_tex2_puff.npz work/rig.json ${PUFFKEEP:-0.0} > /dev/null
python3 scripts/bust_pf4.py work/uv_tex2_puff.npz work/uv_tex2_bust.npz
python3 scripts/eyelid_pf4.py work/uv_tex2_bust.npz work/uv_tex2.npz > /dev/null
scripts/rig_f4.sh work/uv_tex2.npz 2>&1 | grep -E "Error|Trace" || true
scripts/build_runtime.sh $2 2>&1 | grep -E "WINDING|Error|Trace|install|LOD" || true
scripts/viewer_update.sh $1 > /dev/null
echo REBUILT $1
