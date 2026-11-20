#!/bin/bash
# viewer GLBs (ramps baked per tier) + manifest; project folder. Usage: scripts/viewer_update.sh <revision>
mkdir -p review/viewer
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
$G -W ignore scripts/viewer_tiers.py 2>&1 | grep -v Unexpected
$G -W ignore scripts/make_viewer_manifest.py $1 sc_a="Scholar (row 274)"=work/viewer_sc_a.glb sc_b="Master Scholar (row 275)"=work/viewer_sc_b.glb 2>&1 | tail -1 | cut -c1-200
