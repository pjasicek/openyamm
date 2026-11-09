#!/usr/bin/env bash
# Viewer close-ups of the head (default model of review/vtest): front, three-quarter, side, back, low front, chest.
# Usage: head_shots.sh <label>
set -euo pipefail
cd "$(dirname "$0")/../.."
node mm6_dru1_claude/scripts/viewer_shots.mjs "http://127.0.0.1:8901/level_generation/creatures/mm6_dru1_reduce_claude/review/vtest/index.html" \
  mm6_dru1_reduce_claude/review/head/viewer \
  "$1_front:Standing:0:front:head:0,1.58,0.55:0,1.58,0" "$1_q34:Standing:0:front:head:0.4,1.6,0.4:0,1.58,0" \
  "$1_side:Standing:0:front:head:0.55,1.58,0:0,1.58,0" "$1_back:Standing:0:front:head:0,1.6,-0.6:0,1.5,0" \
  "$1_low:Standing:0:front:head:0,1.35,0.6:0,1.55,0" "$1_body:Standing:0:front:body:0,1.3,1.4:0,1.25,0" | tail -1
