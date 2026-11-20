#!/bin/bash
# shots.sh <cow|goat> <tier id> <outdir under review/> spec...   (name:clip:t:view:focus[:cam:target])
cd /home/pjasicek/github/OpenYAMM; n=$1; tier=$2; out=$PWD/level_generation/creatures/mm9_${n}_claude/review/$3; shift 3
mkdir -p $out
node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs "http://127.0.0.1:8912/level_generation/creatures/mm9_${n}_claude/review/viewer/?model=$tier" $out "$@" 2>&1 | grep -v "^$" | cut -c1-120 | tail -n 2
