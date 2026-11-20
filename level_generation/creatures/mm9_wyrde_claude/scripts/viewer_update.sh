#!/bin/bash
# viewer GLBs + manifest; project folder. Usage: scripts/viewer_update.sh <revision>
mkdir -p review/viewer
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
$G -W ignore scripts/viewer_tiers.py 2>&1 | grep -v Unexpected
$G -W ignore scripts/make_viewer_manifest.py $1 wy_young="Morgan, Wyrde of the Unknown (row 265)"=work/viewer_wy_young.glb wy_mature="Verdandi, Wyrde of the Knowing (row 264)"=work/viewer_wy_mature.glb 2>&1 | tail -1 | cut -c1-200
