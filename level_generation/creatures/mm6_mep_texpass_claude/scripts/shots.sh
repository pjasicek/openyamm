#!/usr/bin/env bash
# Identical-camera review-viewer shots, every tier: shots.sh <tag>... -> review/shots/mep_<tier>_<tag>_<name>.png
set -euo pipefail
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/mm6_mep_texpass_claude
SPECS=("face:Standing:0:front:head" "face34:Standing:0:quarter:head" "headback:Standing:0:back:head" "chest:Standing:0:front:shoulders" "back:Standing:0:back:shoulders" "arms:Standing:0:front:arms" "skirt:Standing:0:quarter:skirt" "feet:Standing:0:front:feet" "full:Standing:0:front:body" "fullback:Standing:0:back:body")
for tag in "$@"; do
  for tier in a b c; do
    python3 level_generation/creatures/claude_shared/texpass_viewer_shots.py shots $P $P/review/shots_tmp mep_${tier}_${tag} "${SPECS[@]}" | tail -n 1
  done
done
mkdir -p $P/review/shots && mv $P/review/shots_tmp/*.png $P/review/shots/ && rmdir $P/review/shots_tmp
