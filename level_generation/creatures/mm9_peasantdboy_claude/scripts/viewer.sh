#!/usr/bin/env bash
# Review-viewer GLBs after build_runtime_pdboy.sh (project folder): tiers a and b baked from the delivered body.
# Usage: scripts/viewer.sh <revision>
set -euo pipefail
V=../claude_shared/gltf_venv/bin/python
PYTHONPATH=/usr/lib/python3/dist-packages "$V" scripts/viewer_tiers.py export/mm9_pdboy.glb pdboy_a,pdboy_b 2>/dev/null
python3 scripts/make_viewer_manifest.py "$1" "pdboy_a=Dwarf boy a (row 67 Commoner Child; DWARFBOY1)=review/viewer/pdboy_a.glb" \
  "pdboy_b=Dwarf boy b (row 68 Townsfolk Child; DWARFBOY2)=review/viewer/pdboy_b.glb" | cut -c1-80
