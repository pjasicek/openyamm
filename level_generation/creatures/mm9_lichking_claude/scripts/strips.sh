#!/bin/bash
# frame strips of every clip (seven frames, wide 3/4 camera): scripts/strips.sh
G=../claude_shared/gltf_venv/bin/python
S=$($G -W ignore scripts/strips.py export/mm9_lichking.glb 7 "" st 2>/dev/null | grep -v Unexpected | tr '\n' ' ')
bash scripts/vs.sh lichking review/shots $S
echo done > work/strips.done
