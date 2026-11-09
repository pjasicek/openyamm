#!/bin/bash
# viewer GLBs + manifest; project folder. Usage: scripts/viewer_update.sh <revision>
python3 scripts/viewer_tiers.py
../claude_shared/gltf_venv/bin/python scripts/make_viewer_manifest.py $1 mummy_a="Canopic Mummy"=work/viewer_mummy_a.glb mummy_b="Embalmed Mummy"=work/viewer_mummy_b.glb mummy_c="Petrified Mummy"=work/viewer_mummy_c.glb 2>&1 | tail -1 | cut -c1-100
