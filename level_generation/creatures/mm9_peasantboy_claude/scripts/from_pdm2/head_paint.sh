#!/usr/bin/env bash
# Head-set paint chain (project folder; face pass 2026-11-02). Each step keeps a first-run backup and reads from it;
# scripts/reset_head_backups.py moves the later backups back so the chain re-runs from the composed (preneck) heads:
# fix_neck_pdm2.py (knit on the neck -> skin) -> skin_unify.py (one skin tone over face, forehead, scalp, ears) ->
# project_face.py (Codex eye/brow/mouth repaint, warped by warp_face.py; only when references_face/out_face_<t>_warped.png
# exist) -> hand_clean.py (hands to the face tone) -> fix_ear_pdm2.py (ears: synthesised skin, ties and smudges around
# them removed; ear sweep 2026-11-02) -> pad_head.py.
set -euo pipefail
V=../claude_shared/gltf_venv/bin/python
G=work/pdm2_body_tex.glb
python3 scripts/reset_head_backups.py
"$V" scripts/fix_neck_pdm2.py "$G" pdm2_tp pdm2b_tp 2>/dev/null | grep FIXNECK
for p in pdm2_tp pdm2b_tp; do "$V" scripts/skin_unify.py "$G" $p 2>/dev/null | grep SKIN_UNIFY | cut -c1-160; done
for t in a b; do
  p=$([ $t = a ] && echo pdm2_tp || echo pdm2b_tp)
  if [ -f references_face/out_face_${t}_warped.png ]; then
    PATCH_SPOTS="${PATCH_SPOTS:--0.04,1.037,0.011;-0.022,1.035,0.008;0.023,1.035,0.008}" PATCH_CELLS=work/patch_islands.json FACE_WINDOWS="${FACE_WINDOWS:-1.022,1.11,0.07;0.975,1.05,0.055}" "$V" scripts/project_face.py "$G" $p references_face/out_face_${t}_warped.png 0 1.045 0.26 2>/dev/null | grep PROJECT
  fi
done
HAND_REF=205,118,80 "$V" scripts/hand_clean.py pdm2_tp 2>/dev/null | grep HAND_CLEAN | cut -c1-60
HAND_REF=182,100,70 "$V" scripts/hand_clean.py pdm2b_tp 2>/dev/null | grep HAND_CLEAN | cut -c1-60
"$V" scripts/fix_ear_pdm2.py "$G" pdm2_tp,pdm2b_tp 2>/dev/null | grep FIXEAR | cut -c1-200
"$V" scripts/pad_head.py "$G" pdm2_tp pdm2b_tp 2>/dev/null | grep PAD_HEAD
