#!/bin/bash
# viewer GLB + manifest; project folder. Usage: scripts/viewer_update.sh <revision>
python3 scripts/viewer_tiers.py
../claude_shared/gltf_venv/bin/python scripts/make_viewer_manifest.py $1 lichking="Lich King"=work/viewer_lichking.glb 2>&1 | tail -1 | cut -c1-120
