#!/bin/sh
# X9's L1 brief and drawings: render and measure, write the brief with the census in plan totals, format, validate,
# board. Codex paints separately (paint_x9.py), once, no retries. Runs under a memory cap. tune_chain.py --apply is a
# design aid (equal rope-bridge spans down both chains, the unseen way nine cells); run it only after moving islands.
set -e
cd "$(dirname "$0")"
ROOT=../../../..
OYMAP="$ROOT/openyamm-studio/build-xeen/oymap"
CAP="systemd-run --user --scope -q -p MemoryMax=8G"
$CAP python3 render_x9.py > /dev/null
python3 gen_l1.py --with-census
"$OYMAP" fmt "$ROOT/devdocs/xeen/briefs/x9/L1"
"$OYMAP" fmt --check "$ROOT/devdocs/xeen/briefs/x9/L1"
"$OYMAP" validate "$ROOT/devdocs/xeen/briefs/x9/L1" --assets "$ROOT/assets_dev"
python3 board_x9.py
