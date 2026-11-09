#!/bin/bash
# from the project folder: tier GLBs + manifest. Usage: viewer_update.sh <revision>
V=../claude_shared/gltf_venv/bin/python
$V -W ignore scripts/viewer_tiers.py 2>&1 | tail -1
$V -W ignore scripts/make_viewer_manifest.py "$1" "banshee_a=Fright (Banshee A)=review/viewer/banshee_a.glb" "banshee_b=Dread (Banshee B)=review/viewer/banshee_b.glb" "banshee_c=Terror (Banshee C)=review/viewer/banshee_c.glb" 2>&1 | tail -1 | cut -c1-160
