#!/bin/bash
# MM9 sources: SKRAELOS.abc with its skin (row 257). Repo root.
set -e
P=level_generation/creatures/mm9_skraelos_claude
PYG=level_generation/creatures/claude_shared/gltf_venv/bin/python
M=mm9/extracted/MODELS/MODELS
S=mm9/extracted/SKINS/SKINS
PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id skraelos --scale 0.0256 \
  --texture 0=$S/SKRAELOS.dtx $M/SKRAELOS.abc $P/source/mm9
