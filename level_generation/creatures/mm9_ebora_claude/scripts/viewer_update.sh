#!/bin/bash
# viewer GLBs + manifest; project folder. Usage: scripts/viewer_update.sh <revision>
G=../claude_shared/gltf_venv/bin/python
$G -W ignore scripts/viewer_tiers.py | tail -1
$G -W ignore scripts/make_viewer_manifest.py $1 eb="Ebora (row 301)"=work/viewer_eb.glb s1="Concubine, siren1 (row 302)"=work/viewer_s1.glb s2="Concubine, siren2 (script skin)"=work/viewer_s2.glb s3="Concubine, siren3 (script skin)"=work/viewer_s3.glb s4="Concubine, siren4 (script skin)"=work/viewer_s4.glb 2>&1 | tail -1 | cut -c1-80
