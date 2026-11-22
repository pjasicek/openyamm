#!/bin/sh
# X4's L1 brief and drawings: generate, format, validate, render, board. Codex paints separately (paint_x4.py VIEW).
set -e
cd "$(dirname "$0")"
ROOT=../../../..
python3 gen_l1.py
"$ROOT/openyamm-studio/build-xeen/oymap" fmt "$ROOT/devdocs/xeen/briefs/x4/L1"
"$ROOT/openyamm-studio/build-xeen/oymap" validate "$ROOT/devdocs/xeen/briefs/x4/L1" --assets "$ROOT/assets_dev"
python3 render_x4.py
python3 board_x4.py
