#!/bin/bash
# PF3 rebuild from the paid inputs (project folder): head paint (sym -> fix -> tier B base -> Codex faces projected) -> finish -> tiers ->
# finish -> tweak -> rig (weights_pf3) -> runtime -> viewer. Usage: scripts/rebuild_f3.sh <viewer rev> [--install]
# Inputs that are never regenerated here: work/asm_frozen.npz (= add_parts_pf3.py on F1's frozen mesh), work/uv.npz (uv_pf3.py, then
# fix_lining_uv_pf3.py: the paid head layout; pass 2: reduce_pf3.py decimated veil, braids and the skirt lining into it), textures/pf_*_raw|normal|rough (compose_pf.py), AO bakes, references_face_f3/out_face_*.png.
set -e
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
python3 scripts/finish_pf.py > /dev/null      # uv_tex.npz from the current work/uv.npz
python3 scripts/tweak_pf1.py work/asm_frozen.npz work/uv_tex.npz work/uv_tex2.npz 0.012 8 > /dev/null
$G -W ignore scripts/sym_paint.py work/uv.npz 1 textures/pf_head_a_raw.png textures/pf_head_a_sym.png > /dev/null
$G -W ignore scripts/head_fix_pf3.py textures/pf_head_a_sym.png textures/pf_head_a_fix.png > /dev/null
python3 scripts/tier_b_head_pf3.py textures/pf_head_a_fix.png textures/pf_head_b_fix.png > /dev/null
for t in a b; do
  python3 scripts/align_face_pf3.py references_face_f3/in_face_$t.png references_face_f3/out_face_$t.png references_face_f3/out_face_${t}_aligned.png > /dev/null
  python3 scripts/warp_nose_pf1.py references_face_f3/out_face_${t}_aligned.png references_face_f3/out_face_${t}_nose.png > /dev/null
  N=""; [ $t = a ] && N="--normal textures/pf_head_normal_meshy.png textures/pf_head_normal.png"
  H=""; [ $t = b ] && H=1
  HAIRWIN=$H $G -W ignore scripts/project_face_pf3.py $t references_face_f3/out_face_${t}_nose.png textures/pf_head_${t}_fix.png textures/pf_head_${t}_face.png $N 2>&1 | grep -E "PROJECT|Error|Trace" || true
done
# pass 2: skin harmonised in 3D round the face (ear plates, jaw, under the chin, neck)
for t in a b; do python3 scripts/skin_harmonize_pf3.py $t textures/pf_head_${t}_face.png textures/pf_head_a_sym.png textures/pf_head_${t}_face.png | grep HARMON; done
# pass 3: the hood's front edge one clean line (the part split's zigzag of linen/hair teeth)
for t in a b; do python3 scripts/hood_edge_pf3.py textures/pf_head_${t}_face.png textures/pf_head_${t}_face.png | grep HOODEDGE; done
cp textures/pf_head_b_face.png textures/pf_head_b_final.png
python3 scripts/finish_pf.py > /dev/null
$G -W ignore scripts/tiers_pf3.py 2>&1 | grep -E "Error|Trace" || true
python3 scripts/finish_pf.py > /dev/null
python3 scripts/tweak_pf1.py work/asm_frozen.npz work/uv_tex.npz work/uv_tex2.npz 0.012 8 > /dev/null
python3 scripts/chin_smooth_pf3.py work/uv_tex2.npz work/uv_tex2_chin.npz 16 0.005      # chin crease, ear plates, hood tuck; pass 3: chin/jaw sculpt, nose tip
scripts/rig_f3.sh work/uv_tex2_chin.npz 2>&1 | grep -E "Error|Trace" || true
scripts/build_runtime.sh $2 2>&1 | grep -E "WINDING|Error|Trace|install|LOD" || true
scripts/viewer_update.sh $1 > /dev/null
echo REBUILT $1
