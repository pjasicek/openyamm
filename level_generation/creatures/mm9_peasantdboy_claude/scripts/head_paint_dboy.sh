#!/usr/bin/env bash
# Head-set and body paint finishing chain (project folder), re-run as a whole after any change:
# face_fix_dboy.py (from work/<p>_head_basecolor_composed.png: closed lips, no lipstick) -> hand_clean.py (one clean skin
# colour from the cheek) -> wrist_band_dboy.py (MM9's dark wrist band over the hand graft seam, body + hand texels;
# body from work/pdboy_tp_basecolor_graded_orig.png). Needs work/head_texel_pos.npz and work/pdboy_body_tex.glb.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/face_fix_dboy.py pdboy_tp 0.2 | cut -c1-120
python3 scripts/face_fix_dboy.py pdboyb_tp 0.4 | cut -c1-120
for p in pdboy_tp pdboyb_tp; do HAND_REF=$(cat work/hand_ref_$p.txt) python3 scripts/hand_clean.py $p 1.0 | tail -1 | cut -c1-80; done
PYTHONPATH=/usr/lib/python3/dist-packages ../claude_shared/gltf_venv/bin/python scripts/wrist_band_dboy.py work/pdboy_body_tex.glb pdboy_tp pdboyb_tp 2>&1 | grep WRISTBAND
