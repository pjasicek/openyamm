#!/bin/bash
# Viewer shots with retries. Usage: scripts/shots.sh <out dir> spec...   Project folder. spec: name:clip:t:view:focus[:cx,cy,cz:tx,ty,tz]
U=http://127.0.0.1:8912/level_generation/creatures/mm9_kira_claude/review/viewer/; V=../mm8_m424_claude/scripts/viewer_shots.mjs; d=$1; shift 1
for i in 1 2 3; do r=$(timeout 300 node $V "$U?model=${M:-kira}" $PWD/$d "$@" 2>&1 | tail -1); [[ "$r" == SHOTS* ]] && { echo "$r"; exit 0; }; done; echo "FAILED: $r"; exit 1
