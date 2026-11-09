#!/usr/bin/env bash
# Head-set paint chain (project folder). compose_headhand.py's output is kept as textures/pdm4_tp_head_*_preemblem.png
# (emblem_project.py's first-run backup); every run restarts from it:
# emblem_project.py (the cap's silver medallion from references_head/01_front.png; scripts/emblem_overlay.py) ->
# hand_clean.py (hands to the face tone, HAND_REF = the forehead skin of the paint) -> pad_head.py.
set -euo pipefail
V=../claude_shared/gltf_venv/bin/python
G=work/pdm4_body_tex.glb
for m in basecolor normal_1k; do
  [ -f textures/pdm4_tp_head_${m}_preemblem.png ] && cp textures/pdm4_tp_head_${m}_preemblem.png textures/pdm4_tp_head_${m}.png
done
"$V" scripts/emblem_project.py "$G" pdm4_tp references_face/emblem_overlay.png 0 1.05 0.30 2>/dev/null | grep EMBLEM
HAND_REF=196,121,94 "$V" scripts/hand_clean.py pdm4_tp 1.0 2>/dev/null | grep HAND_CLEAN | cut -c1-120
"$V" scripts/pad_head.py "$G" pdm4_tp 2>/dev/null | grep PAD_HEAD
