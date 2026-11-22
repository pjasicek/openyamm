#!/bin/sh
# X7's L1 brief and drawings: generate, format, render, write the census into plan totals, validate, board.
# Codex paints separately (paint_x7.py VIEW), once per view, no retries. Runs under a memory cap.
set -e
cd "$(dirname "$0")"
ROOT=../../../..
OYMAP="$ROOT/openyamm-studio/build-xeen/oymap"
CAP="systemd-run --user --scope -q -p MemoryMax=8G"
python3 gen_l1.py
"$OYMAP" fmt "$ROOT/devdocs/xeen/briefs/x7/L1"
$CAP python3 render_x7.py > /dev/null
python3 gen_l1.py --with-census
"$OYMAP" fmt "$ROOT/devdocs/xeen/briefs/x7/L1"
"$OYMAP" validate "$ROOT/devdocs/xeen/briefs/x7/L1" --assets "$ROOT/assets_dev"
$CAP python3 render_x7.py
python3 board_x7.py
