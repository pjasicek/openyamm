#!/bin/bash
# viewer GLBs + manifest; project folder. Usage: scripts/viewer_update.sh <revision>
mkdir -p review/viewer
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
$G -W ignore scripts/viewer_tiers_pg.py mm9_peasantgirl.glb pg_ramps_h.json 2>&1 | grep -v Unexpected
$G -W ignore scripts/viewer_tiers_pg.py mm9_peasantgirl1e.glb pg_ramps_e.json 2>&1 | grep -v Unexpected
$G -W ignore scripts/make_viewer_manifest.py $1 pg_g2="Commoner Child, PeasantGirl2 (row 71)"=work/viewer_pg_g2.glb pg_g3="Townsfolk Child, PeasantGirl3 (row 72)"=work/viewer_pg_g3.glb pg_g1e="Townsfolk Child, elf PeasantGirl1e (row 74)"=work/viewer_pg_g1e.glb 2>&1 | tail -1 | cut -c1-200
