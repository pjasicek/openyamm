#!/bin/bash
# viewer face shots + sheets for both tiers. Usage (project folder): scripts/quick_face.sh <rev tag>
set -e
G=../claude_shared/gltf_venv/bin/python; PYTHONPATH=/usr/lib/python3/dist-packages $G -W ignore scripts/face_specs.py export/mm9_scholar.glb $1 Standing:0 0,0.07,0.06 "Bip01 Head" > work/face_specs_$1.txt
for t in a b; do
  scripts/vs.sh sc_$t review/face_$1_$t $(cat work/face_specs_$1.txt)
  python3 scripts/face_sheet.py review/face_$1_$t $1 review/face_$1_${t}_sheet.png references_hd/mm9_head_views_$([ $t = a ] && echo 1 || echo 3).png
done
