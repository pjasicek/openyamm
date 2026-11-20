#!/bin/bash
# PF3 pass 5 rebuild (project folder; run under the memory cap): the head paints are fresh Meshy 4K retextures per tier on the current head
# mesh and UVs (pf3_head_p5_a / _b -> textures/pf_head_p5{a,b}_raw|normal|rough by compose_pf.py), no projected Codex face.
# tweak -> per tier: sym_paint -> head_fix_pf3 (FRESH: eye rims, ear specks, neck, veil cleanup only) -> [B: braids from A] ->
# skin_harmonize -> hood_edge -> finish -> tiers -> rig -> runtime -> viewer. Usage: scripts/rebuild_f3_p5.sh <viewer rev> [--install]
set -e
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
python3 scripts/finish_pf.py > /dev/null
python3 scripts/tweak_pf1.py work/asm_frozen.npz work/uv_tex.npz work/uv_tex2.npz 0.012 8 > /dev/null
for t in a b; do
  $G -W ignore scripts/sym_paint.py work/uv.npz 1 textures/pf_head_p5${t}_raw.png textures/pf_head_p5${t}_sym.png > /dev/null
  FRESH=1 $G -W ignore scripts/head_fix_pf3.py textures/pf_head_p5${t}_sym.png textures/pf_head_${t}_face.png > /dev/null
done
for t in a b; do python3 scripts/eye_lip_clean_pf3.py textures/pf_head_${t}_face.png textures/pf_head_${t}_face.png; done
python3 scripts/braid_b_pf3.py textures/pf_head_a_face.png textures/pf_head_b_face.png textures/pf_head_b_face.png
# skin_harmonize_pf3.py and hood_edge_pf3.py (passes 2-4) repaired the projected face; on the fresh paint they turned the blonde hair at
# the temples into skin, so they are not run (set P5_HARMONIZE=1 to try them)
if [ -n "${P5_HARMONIZE:-}" ]; then
  for t in a b; do python3 scripts/skin_harmonize_pf3.py $t textures/pf_head_${t}_face.png textures/pf_head_p5${t}_sym.png textures/pf_head_${t}_face.png | grep HARMON; done
  for t in a b; do python3 scripts/hood_edge_pf3.py textures/pf_head_${t}_face.png textures/pf_head_${t}_face.png | grep HOODEDGE; done
fi
cp textures/pf_head_p5a_rough.png textures/pf_head_rough.png
python3 scripts/flatten_face_normal_pf3.py textures/pf_head_p5a_normal.png textures/pf_head_normal.png 0.85
cp textures/pf_head_b_face.png textures/pf_head_b_final.png
python3 scripts/finish_pf.py > /dev/null
$G -W ignore scripts/tiers_pf3.py 2>&1 | grep -E "Error|Trace" || true
python3 scripts/finish_pf.py > /dev/null
python3 scripts/tweak_pf1.py work/asm_frozen.npz work/uv_tex.npz work/uv_tex2.npz 0.012 8 > /dev/null
python3 scripts/chin_smooth_pf3.py work/uv_tex2.npz work/uv_tex2_chin.npz 16 0.005 > /dev/null
# collapsed slivers (closed lip slit, small holes) whose corners sit in different UV islands sample one texel each
python3 scripts/uv_sliver_fix_pf3.py work/uv_tex2_chin.npz work/uv_tex2_chin.npz textures/pf_head_a_face.png
# island gutters take their island edge's colour (the lip-midline glint and eye-corner slivers sampled the paint's own gutter colours)
python3 scripts/gutter_fill_pf3.py work/uv_tex2_chin.npz textures/pf_head_a_face.png textures/pf_head_b_face.png textures/pf_head_normal.png textures/pf_head_orm.png
scripts/rig_f3.sh work/uv_tex2_chin.npz 2>&1 | grep -E "Error|Trace" || true
scripts/build_runtime.sh $2 2>&1 | grep -E "WINDING|Error|Trace|install|LOD" || true
scripts/viewer_update.sh $1 > /dev/null
echo REBUILT $1
