#!/usr/bin/env bash
# Viewer GLBs + manifest from the delivered export (tiers baked per material for three.js). Usage (project folder): scripts/retier.sh <revision>
set -euo pipefail
V=../claude_shared/gltf_venv/bin/python
"$V" scripts/viewer_tiers.py 2>/dev/null
python3 scripts/make_viewer_manifest.py "$1" "pdm3_b=Tier B (row 11 Town; PEASANTDM3B, the shared paint)=review/viewer/pdm3_b.glb" "pdm3_a=Tier A (row 12 Shopkeeper; PEASANTDM3A)=review/viewer/pdm3_a.glb" | cut -c1-80
