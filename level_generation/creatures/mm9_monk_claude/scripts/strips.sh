#!/bin/bash
# frame strips of every clip for one tier: scripts/strips.sh a|b|c
t=$1; G=../claude_shared/gltf_venv/bin/python
S=$($G -W ignore scripts/strips.py export/mm9_monk.glb 6 "" st$t 2>/dev/null | grep -v Unexpected | tr '\n' ' ')
scripts/vs.sh mk_$t review/shots $S
echo done > work/strips_$t.done
