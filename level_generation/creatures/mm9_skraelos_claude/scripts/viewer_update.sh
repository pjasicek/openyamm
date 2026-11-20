#!/bin/bash
# viewer GLB + manifest; project folder. Usage: scripts/viewer_update.sh <revision>
mkdir -p review/viewer
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
$G -W ignore scripts/viewer_sk.py 2>&1 | grep -v Unexpected
$G -W ignore scripts/make_viewer_manifest_sk.py $1 sk="Skraelos (row 257)"=work/viewer_sk.glb 2>&1 | tail -1 | cut -c1-200
