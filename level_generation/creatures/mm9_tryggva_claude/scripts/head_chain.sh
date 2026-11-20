#!/usr/bin/env bash
# Head + hands set paint chain after compose_headhand.py (project folder): fringe_fix.py (hair-shell rim, forehead band) ->
# hairline_fix.py (face shell above the hair edge -> hair) -> hand_clean.py -> project_face.py -> face_touch.py ->
# fix_ear_try.py. Each step's backup is cleared first so a re-run chains from the composed head colour (work/try_tp_head_basecolor_composed.png).
set -euo pipefail
V=../claude_shared/gltf_venv/bin/python
if [[ -f work/try_tp_head_basecolor_composed.png ]]; then cp work/try_tp_head_basecolor_composed.png textures/try_tp_head_basecolor.png; fi
rm -f work/try_tp_head_basecolor_prehairline.png work/try_tp_head_basecolor_prehand.png
HAIR_MIN_Y=1.56 "$V" scripts/fringe_fix.py 2>/dev/null | grep FRINGE
"$V" scripts/hairline_fix.py ${HAIRLINE:-1.700 1.716} 2>/dev/null | grep HAIRLINE
"$V" scripts/hand_clean.py 2>/dev/null | tail -1
# face pass: Codex eye-area + parting-notch repaint (references_face/out_face.png, scripts/codex_face.sh) projected from the front
rm -f textures/try_tp_head_basecolor_preface.png
TOP_WIN=1.696,1.735,0.05 "$V" scripts/project_face.py export/mm9_try.glb try_tp references_face/out_face.png 2>/dev/null
# chin rim and the tear streak under the left eye (face_touch.py, after the projection)
rm -f textures/try_tp_head_basecolor_pretouch.png
"$V" scripts/face_touch.py export/mm9_try.glb 2>/dev/null
# ears (ear sweep 2026-11-02): undo fringe_fix on the ear faces of the hair shell, clear Meshy's hair paint on and below them
rm -f textures/try_tp_head_basecolor_preear.png textures/try_tp_head_normal_1k_preear.png
"$V" scripts/fix_ear_try.py 2>/dev/null | grep FIXEAR
