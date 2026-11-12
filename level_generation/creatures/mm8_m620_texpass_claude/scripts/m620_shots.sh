#!/usr/bin/env bash
# Identical-camera review-viewer shots of the m620 pass, every tier: m620_shots.sh <tag> [<tag>...] -> review/shots/<tier>_<tag>_<name>.png
set -euo pipefail
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/mm8_m620_texpass_claude
SPECS=(
 "face:Standing:0:front:head:0,1.6,0.42:-0.02,1.58,-0.02"
 "face34:Standing:0:front:head:0.3,1.6,0.3:-0.02,1.58,-0.02"
 "hairback:Standing:0:front:head:-0.1,1.7,-0.5:-0.02,1.6,-0.02"
 "chest:Standing:0:front:body:0,1.2,0.75:0,1.15,0"
 "back:Standing:0:front:body:0,1.15,-0.8:0,1.1,0"
 "hand:Standing:0:front:body:0.6,0.95,0.45:0.27,0.87,0.09"
 "legs:Standing:0:front:body:0.2,0.55,1.1:0,0.5,0"
 "full:Standing:0:front:body"
 "fullback:Standing:0:back:body"
)
for tag in "$@"; do
  for tier in a b c; do
    python3 level_generation/creatures/claude_shared/texpass_viewer_shots.py shots $P $P/review/shots_tmp bedraggled_${tier}_${tag} "${SPECS[@]}" | tail -n 1
  done
done
mkdir -p $P/review/shots && mv $P/review/shots_tmp/*.png $P/review/shots/ && rmdir $P/review/shots_tmp
