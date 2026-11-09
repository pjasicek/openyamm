#!/usr/bin/env bash
# Head-set paint finishing chain (project folder), re-run as a whole after any change: face_fix_dboy.py (from
# work/sig_tp_head_basecolor_composed.png: closed mouth, lips toward the cheek hue; LIP = rest y 1.557) -> eye_rims.py (no red
# rims, softened bags) -> hand_clean.py (one clean skin colour from the cheek: compose_headhand's reference had caught the
# blond hair and painted the hands yellow). Needs work/head_texel_pos.npz (head_texel_pos.py on work/sig_body_tex.glb).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/face_fix_dboy.py sig_tp 0.15 1.557 | cut -c1-160
python3 scripts/eye_rims.py sig_tp 1.588 1.622
python3 scripts/chin_spot.py sig_tp
HAND_REF=$(cat work/hand_ref_sig_tp.txt) python3 scripts/hand_clean.py sig_tp 1.0 | tail -1 | cut -c1-100
