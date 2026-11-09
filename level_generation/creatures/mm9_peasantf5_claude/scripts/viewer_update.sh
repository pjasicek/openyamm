#!/bin/bash
# viewer GLBs + manifest; project folder. Usage: scripts/viewer_update.sh <revision>
mkdir -p review/viewer
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
$G -W ignore scripts/viewer_tiers.py 2>&1 | grep -v Unexpected
$G -W ignore scripts/make_viewer_manifest.py $1 pf5_b="Commoner, grey-haired woman (row 36)"=work/viewer_pf5_b.glb pf5_a="Shopkeeper, auburn-haired woman (rows 34, 41)"=work/viewer_pf5_a.glb 2>&1 | tail -1 | cut -c1-200
