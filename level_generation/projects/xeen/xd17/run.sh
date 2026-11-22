#!/bin/sh
# XD-17's L1 brief and drawings: generate, format, render, write the census into plan totals, validate, board.
# Codex paints separately (paint_xd17.py VIEW), once per view, no retries. Runs under a memory cap.
set -e
cd "$(dirname "$0")"
ROOT=../../../..
OYMAP="$ROOT/openyamm-studio/build-xeen/oymap"
CAP="systemd-run --user --scope -q -p MemoryMax=8G"
python3 gen_l1.py
"$OYMAP" fmt "$ROOT/devdocs/xeen/briefs/xd17/L1"
$CAP python3 render_xd17.py > /dev/null
python3 gen_l1.py --with-census
"$OYMAP" fmt "$ROOT/devdocs/xeen/briefs/xd17/L1"
"$OYMAP" fmt --check "$ROOT/devdocs/xeen/briefs/xd17/L1"
"$OYMAP" validate "$ROOT/devdocs/xeen/briefs/xd17/L1" --assets "$ROOT/assets_dev"
$CAP python3 board_xd17.py
