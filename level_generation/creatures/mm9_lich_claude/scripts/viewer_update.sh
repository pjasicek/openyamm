#!/bin/bash
# from the project folder: tier GLBs + manifest. Usage: viewer_update.sh <revision>
V=../claude_shared/gltf_venv/bin/python
$V -W ignore scripts/viewer_tiers.py lich 2>&1 | tail -1
$V -W ignore scripts/make_viewer_manifest.py "$1" "lich_a=Lich (Lich A)=review/viewer/lich_a.glb" "lich_b=Power Lich (Lich B)=review/viewer/lich_b.glb" 2>&1 | tail -1 | cut -c1-120
