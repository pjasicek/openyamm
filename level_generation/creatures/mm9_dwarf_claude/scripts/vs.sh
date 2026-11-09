#!/bin/bash
# viewer shots: scripts/vs.sh <tier id> <outdir> spec... (spec name:clip:t:view:focus[:cx,cy,cz:tx,ty,tz]). Project folder.
t=$1; out=$2; shift 2; mkdir -p $out
node ../mm8_m424_claude/scripts/viewer_shots.mjs "http://127.0.0.1:8912/level_generation/creatures/mm9_dwarf_claude/review/viewer/?model=$t" $PWD/$out "$@" 2>&1 | tail -1 | cut -c1-120
