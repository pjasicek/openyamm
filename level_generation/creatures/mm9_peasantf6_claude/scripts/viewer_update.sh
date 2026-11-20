#!/bin/bash
# viewer GLBs + manifest; project folder. Usage: scripts/viewer_update.sh <revision>
mkdir -p review/viewer
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
$G -W ignore scripts/viewer_tiers.py 2>&1 | grep -v Unexpected
$G -W ignore scripts/make_viewer_manifest.py $1 pf6_a="Town, young blonde elf woman (row 17)"=work/viewer_pf6_a.glb pf6_b="Shopkeeper, auburn elf woman (row 19)"=work/viewer_pf6_b.glb 2>&1 | tail -1 | cut -c1-200
