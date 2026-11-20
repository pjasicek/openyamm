#!/bin/bash
# Tier C head colour (project folder), 0 credits: Codex's repaint of the flat front render of tier D's final head
# (references_face/out_face_c.png) -> fit_face_c.py (nose/mouth widths, catchlights, edge colour match) -> face_front.py project onto
# tier D's final head colour -> eye_fix.py (lighter under-eye lift) -> textures/pm2d_head_c_final.png. No mouth_fix.py: the repaint
# was drawn on D's fixed mouth and the projection covers the visible lip strip with the repaint's own closed-smile line.
set -e
python3 scripts/fit_face_c.py references_face/out_face_c.png references_face/out_face_c_fit.png 0.68 0.84 references_face/in_face_c.png 0.35
python3 scripts/face_front.py project references_face/out_face_c_fit.png textures/pm2d_head_d_final.png work/head_c_proj.png --report work/head_c_proj.json
python3 scripts/eye_fix.py work/head_c_proj.png textures/pm2d_head_c_final.png 0.65 0.4
