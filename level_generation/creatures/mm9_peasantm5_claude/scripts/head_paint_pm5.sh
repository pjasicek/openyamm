#!/bin/bash
# M5 head-paint chain (project folder), always from the composed head set (work/pm5_tp_head_basecolor_composed.png =
# compose_head_texpass.py mk_tp pm5_tp meshy/head_retexture_pm5): lash-line sliver under the right eye refilled from the skin
# below the lid (spot_fix_pm5.py, NO generic pass: the brown irises read as beard specks), hands one clean skin colour
# (hand_clean_pm5.py), gutters re-padded (pad_head_pm5.py).
set -e
cd "$(dirname "$0")/.."
G="env PYTHONPATH=/usr/lib/python3/dist-packages ../claude_shared/gltf_venv/bin/python"
cp work/pm5_tp_head_basecolor_composed.png textures/pm5_tp_head_basecolor.png
NEAR_R=0.02 NO_GENERIC=1 $G scripts/spot_fix_pm5.py 2>&1 | grep SPOT_FIX
$G scripts/hand_clean_pm5.py 2>&1 | grep HAND_CLEAN
$G scripts/pad_head_pm5.py 2>&1 | grep PAD_HEAD
python3 scripts/normal_sliver.py textures/pm5_tp_head_normal_1k.png
