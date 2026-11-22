#!/bin/sh
# D7's L1 brief, drawings and board (A6 sub-agent, 2026-11-21): render and measure, check the fall landings against the
# installed Darkside scenes, write the brief with the census in plan totals, format, validate, board. Codex paints
# separately (level_generation/xeen_art/phase6/d7_paint.py arrival|signature), once per view, no retries. The Python
# steps run under a memory cap.
set -e
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT/level_generation/xeen_art/phase6"
OYMAP="$ROOT/openyamm-studio/build-xeen/oymap"
CAP="systemd-run --user --scope -q -p MemoryMax=8G env OPENBLAS_NUM_THREADS=1"
$CAP python3 d7_render.py
$CAP python3 d7_falls.py > /dev/null
$CAP python3 d7_brief.py
"$OYMAP" fmt "$ROOT/devdocs/xeen/briefs/d7/L1"
"$OYMAP" fmt --check "$ROOT/devdocs/xeen/briefs/d7/L1"
"$OYMAP" validate "$ROOT/devdocs/xeen/briefs/d7/L1" --assets "$ROOT/assets_dev"
$CAP python3 board_d7.py
