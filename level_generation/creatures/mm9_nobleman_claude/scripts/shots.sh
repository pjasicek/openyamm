#!/bin/bash
# Viewer shots with retries (the viewer's load times out under the night's load). Usage: scripts/shots.sh <tier a|b|c> <out dir> spec...   Project folder.
U=http://127.0.0.1:8912/level_generation/creatures/mm9_nobleman_claude/review/viewer/; V=../mm8_m424_claude/scripts/viewer_shots.mjs; t=$1; d=$2; shift 2
for i in 1 2 3 4; do r=$(timeout 170 node $V "$U?model=nb_$t" $PWD/$d "$@" 2>&1 | tail -1); [[ "$r" == SHOTS* ]] && { echo "$r"; exit 0; }; done; echo "FAILED $t: $r"; exit 1
