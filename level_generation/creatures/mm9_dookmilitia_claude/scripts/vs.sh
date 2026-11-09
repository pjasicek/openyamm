#!/bin/bash
# viewer shots with custom cameras: scripts/vs.sh <tier> <outdir> spec... (spec name:clip:t:front:body:cx,cy,cz:tx,ty,tz)
t=$1; out=$2; shift 2
cd /home/pjasicek/github/OpenYAMM
node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs "http://127.0.0.1:8912/level_generation/creatures/mm9_dookmilitia_claude/review/viewer/?model=$t" $PWD/level_generation/creatures/mm9_dookmilitia_claude/$out "$@" 2>&1 | tail -1 | cut -c1-100
