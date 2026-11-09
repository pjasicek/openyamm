#!/bin/bash
# viewer GLB + manifest; project folder. Usage: scripts/viewer_update.sh <revision>
mkdir -p review/viewer
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
$G -W ignore scripts/viewer_wo.py 2>&1 | grep -v Unexpected
$G -W ignore scripts/make_viewer_manifest.py $1 wo="Igrid, Wyrde of the Known (row 263)"=work/viewer_wo.glb 2>&1 | tail -1 | cut -c1-200
