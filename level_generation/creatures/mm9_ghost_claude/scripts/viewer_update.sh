#!/bin/bash
# from the project folder: tier GLBs + manifest. Usage: viewer_update.sh <revision>
V=../claude_shared/gltf_venv/bin/python
$V -W ignore scripts/viewer_tiers.py 2>&1 | tail -1
$V -W ignore scripts/make_viewer_manifest.py "$1" "ghost_b=Apparition (Ghost B)=review/viewer/ghost_b.glb" "ghost_a=Shadow (Ghost A)=review/viewer/ghost_a.glb" "ghost_c=Specter (Ghost C)=review/viewer/ghost_c.glb" 2>&1 | tail -1 | cut -c1-160
