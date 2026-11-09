#!/bin/bash
# viewer GLBs + manifest; project folder. Usage: scripts/viewer_update.sh <revision>
python3 scripts/viewer_tiers.py
../claude_shared/gltf_venv/bin/python scripts/make_viewer_manifest.py $1 es_a="Evil Apprentice"=work/viewer_es_a.glb es_b="Evil Sorcerer"=work/viewer_es_b.glb es_c="Evil Grand Sorcerer"=work/viewer_es_c.glb 2>&1 | tail -1 | cut -c1-100
