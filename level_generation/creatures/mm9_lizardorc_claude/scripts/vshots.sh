#!/bin/bash
# direct viewer shots with optional camera:target (project folder). Usage: TIER= scripts/vshots.sh name:clip:t:view:focus[:cam:target] ...  writes review/shots
U=http://127.0.0.1:8912/level_generation/creatures/mm9_lizardorc_claude/review/${VIEW:-viewer}/
exec node ../mm8_m424_claude/scripts/viewer_shots.mjs "$U${TIER:+?model=$TIER}" review/shots "$@"
