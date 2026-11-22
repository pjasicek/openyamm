#!/bin/sh
# P5's L1 brief and drawings: render and measure, write the brief with the census in plan totals, format, validate,
# board. Codex paints separately (paint_p5.py walk|shrine), once per view, no retries. Runs under a memory cap.
set -e
cd "$(dirname "$0")"
ROOT=../../../..
OYMAP="$ROOT/openyamm-studio/build-xeen/oymap"
CAP="systemd-run --user --scope -q -p MemoryMax=8G"
$CAP python3 render_p5.py > /dev/null
python3 gen_l1.py --with-census
"$OYMAP" fmt "$ROOT/devdocs/xeen/briefs/p5/L1"
"$OYMAP" fmt --check "$ROOT/devdocs/xeen/briefs/p5/L1"
"$OYMAP" validate "$ROOT/devdocs/xeen/briefs/p5/L1" --assets "$ROOT/assets_dev"
$CAP python3 board_p5.py
