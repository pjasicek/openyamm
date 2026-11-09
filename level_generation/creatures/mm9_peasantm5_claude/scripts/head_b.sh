#!/bin/bash
# Tier B head colour (project folder), 0 credits: A's final head set -> hair + beard recoloured to MM9 B's golden-brown
# (face_b.py hair) -> Codex repaint of the flat front render (references_face/, brief there) projected inside the face window
# (face_b.py project) -> textures/pm5b_tp_head_basecolor.png; B shares A's head normal (copied) and ORM.
set -e
cd "$(dirname "$0")/.."
G="env PYTHONPATH=/usr/lib/python3/dist-packages ../claude_shared/gltf_venv/bin/python"
$G scripts/face_b.py hair textures/pm5_tp_head_basecolor.png work/pm5b_head_hair.png source/mm9/skins/pm5b.png 2>&1 | grep HAIR_B
$G scripts/face_b.py project references_face/out_face_b.png work/pm5b_head_hair.png textures/pm5b_tp_head_basecolor.png 2>&1 | grep PROJECT
cp textures/pm5_tp_head_normal_1k.png textures/pm5b_tp_head_normal_1k.png
# the lash-line sliver under the right eye refilled from B's own skin below the lid (as head_paint_pm5.sh does for A)
HEADTEX_PNG=textures/pm5b_tp_head_basecolor.png NEAR_R=0.02 NO_GENERIC=1 $G scripts/spot_fix_pm5.py 2>&1 | grep "SPOT_FIX tri"
