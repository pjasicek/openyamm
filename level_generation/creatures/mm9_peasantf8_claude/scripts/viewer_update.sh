#!/bin/bash
# viewer GLBs + manifest; project folder. Usage: scripts/viewer_update.sh <revision>
mkdir -p review/viewer
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
$G -W ignore scripts/viewer_tiers.py 2>&1 | grep -v Unexpected
$G -W ignore scripts/make_viewer_manifest.py $1 pf8_b="Commoner B face (rows 15, 21)"=work/viewer_pf8_b.glb pf8_a="Commoner A face (row 16)"=work/viewer_pf8_a.glb 2>&1 | tail -1 | cut -c1-200
