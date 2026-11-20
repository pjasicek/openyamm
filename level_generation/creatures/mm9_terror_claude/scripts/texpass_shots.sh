#!/usr/bin/env bash
# Texture pass: identical review-viewer shots of every tier. Usage: TOKEN=<lease> PORT=<http port> texpass_shots.sh <before|after>
# Output: review/texpass_viewer/<stage>/<tier>_<shot>.png (run_creature_review.py writes to review/shots first).
set -euo pipefail
stage="$1"; repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"; cd "$repo"
P=level_generation/creatures/mm9_terror_claude
mkdir -p $P/review/texpass_viewer/$stage
for tier in terror_a terror_b terror_c; do
  python3 tools/run_creature_review.py --project $P --token "$TOKEN" --tier $tier --port "${PORT:-8931}" shots \
    tp_full_q:Standing:0:quarter:body tp_full_r:Standing:0:rear:body tp_face_q:Standing:0:quarter:shoulders \
    tp_face_f:Standing:0:front:shoulders tp_macro:Standing:0:front:head tp_belly:Standing:0:quarter:arms \
    tp_legs:Standing:0:front:skirt tp_feet:Standing:0:quarter:feet tp_mouth1:AttackRanged:0.5625:front:shoulders \
    tp_mouth2:AttackMelee:0.604:quarter:shoulders
  for f in $P/review/shots/tp_*.png; do b="$(basename "$f")"; mv "$f" "$P/review/texpass_viewer/$stage/${tier}_${b#tp_}"; done
done
