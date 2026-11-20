#!/bin/bash
# Viewer-lit face sheet (the user's review): front close-up, 3/4, both true profiles, low 3/4 from below, under the jaw, party
# view (2.4 m, eye height 1.75), for Standing 0 and Talk 2.0. Usage (project folder): scripts/face_shots.sh <out dir> [head y 1.62]
set -e
O=$1; Y=${2:-1.57}; U=http://127.0.0.1:8912/level_generation/creatures/$(basename $(pwd))/review/viewer/
S=""
for c in Standing:0 Talk:2.0; do n=${c%%:*}; t=${c##*:}
  S="$S ${n}_front:$n:$t:front:head:0,$Y,0.5:0,$Y,0"
  S="$S ${n}_q34:$n:$t:quarter:head:-0.36,$Y,0.38:0,$Y,0"
  S="$S ${n}_profR:$n:$t:right:head:-0.5,$Y,0:0,$Y,0"
  S="$S ${n}_profL:$n:$t:left:head:0.5,$Y,0:0,$Y,0"
  S="$S ${n}_low:$n:$t:quarter:head:-0.22,$(python3 -c "print($Y-0.3)"),0.34:0,$Y,0"
  S="$S ${n}_party:$n:$t:front:body:0,1.75,2.4:0,1.45,0"
  S="$S ${n}_partyhead:$n:$t:front:head:0,1.75,2.4:0,1.55,0"
done
timeout 600 node scripts/viewer_shots.mjs $U $O $S
