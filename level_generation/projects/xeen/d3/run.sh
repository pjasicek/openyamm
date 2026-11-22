#!/bin/sh
# D3's L1 brief and drawings: generate, format, validate, render, write the census into plan totals, board.
# Codex paints separately (paint_d3.py VIEW), once per view, no retries.
set -e
cd "$(dirname "$0")"
ROOT=../../../..
python3 gen_l1.py
"$ROOT/openyamm-studio/build-xeen/oymap" fmt "$ROOT/devdocs/xeen/briefs/d3/L1"
python3 render_d3.py > /dev/null
python3 gen_l1.py --with-census
"$ROOT/openyamm-studio/build-xeen/oymap" fmt "$ROOT/devdocs/xeen/briefs/d3/L1"
"$ROOT/openyamm-studio/build-xeen/oymap" validate "$ROOT/devdocs/xeen/briefs/d3/L1" --assets "$ROOT/assets_dev"
python3 render_d3.py
if [ -f board_d3.py ]; then python3 board_d3.py; fi
