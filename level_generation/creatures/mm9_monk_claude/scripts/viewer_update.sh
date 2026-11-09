#!/bin/bash
# viewer GLBs + manifest; project folder. Usage: scripts/viewer_update.sh <revision>
mkdir -p review/viewer
python3 scripts/viewer_tiers.py
../claude_shared/gltf_venv/bin/python scripts/make_viewer_manifest.py $1 mk_a="Initiate"=work/viewer_mk_a.glb mk_b="Monk"=work/viewer_mk_b.glb mk_c="Reverend Monk"=work/viewer_mk_c.glb 2>&1 | tail -1 | cut -c1-100
