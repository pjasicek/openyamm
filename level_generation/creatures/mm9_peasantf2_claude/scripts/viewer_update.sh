#!/bin/bash
# viewer GLBs + manifest; project folder. Usage: scripts/viewer_update.sh <revision>
mkdir -p review/viewer
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
$G -W ignore scripts/viewer_tiers.py 2>&1 | grep -v Unexpected
$G -W ignore scripts/make_viewer_manifest.py $1 pf2_a="Town A (rows 31, 38)"=work/viewer_pf2_a.glb pf2_b="Town B (rows 32, 39)"=work/viewer_pf2_b.glb 2>&1 | tail -1 | cut -c1-200
