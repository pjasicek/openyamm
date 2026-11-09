#!/bin/bash
# PF1 rebuild from the paid inputs after the paint steps (project folder): finish -> tiers -> finish -> tweak -> rig -> runtime -> viewer. Usage: scripts/rebuild.sh <viewer rev> [--install]
set -e
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
# head paint: fixes, then the Codex face repaint projected (references_face/, face fix 2026-11-02)
python3 scripts/tweak_pf1.py work/asm_frozen.npz work/uv_tex.npz work/uv_tex2.npz 0.012 8 > /dev/null
# nose fix 2026-11-02: the repaint's nose fitted to the geometry's (tier A takes tier B's nose, its own was two flaps)
python3 scripts/warp_nose_pf1.py references_face/out_face_b_aligned.png references_face/out_face_b_nose.png > /dev/null
python3 scripts/warp_nose_pf1.py references_face/out_face_a_aligned.png references_face/out_face_a_nose.png --nose-from references_face/out_face_b_aligned.png > /dev/null
for t in b a; do
  $G -W ignore scripts/head_fix_pf1.py textures/pf_head_${t}_sym.png textures/pf_head_${t}_fix.png > /dev/null
  N=""; [ $t = b ] && N="--normal textures/pf_head_normal_meshy.png textures/pf_head_normal.png"
  $G -W ignore scripts/project_face_pf1.py $t references_face/out_face_${t}_nose.png textures/pf_head_${t}_fix.png textures/pf_head_${t}_face.png $N 2>&1 | grep -E "PROJECT|NOSE|FIN|EAR|EYE|Error|Trace" || true
done
python3 scripts/finish_pf.py > /dev/null
$G -W ignore scripts/tiers_pf1.py 2>&1 | grep -E "Error|Trace" || true
python3 scripts/finish_pf.py > /dev/null
python3 scripts/tweak_pf1.py work/asm_frozen.npz work/uv_tex.npz work/uv_tex2.npz 0.012 8 > /dev/null
scripts/rig.sh work/uv_tex2.npz 2>&1 | grep -E "Error|Trace" || true
scripts/build_runtime.sh $2 2>&1 | grep -E "WINDING|Error|Trace|install" || true
echo REBUILT $1
