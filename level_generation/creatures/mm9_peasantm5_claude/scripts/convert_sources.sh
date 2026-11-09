#!/bin/bash
# MM9 sources: PEASANTM5.abc with both skins (A, B). Repo root.
set -e
P=level_generation/creatures/mm9_peasantm5_claude
PYG=level_generation/creatures/claude_shared/gltf_venv/bin/python
M=mm9/extracted/MODELS/MODELS
S=mm9/extracted/SKINS/SKINS
for t in a b; do
  T=$(echo $t | tr a-z A-Z)
  PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id pm5$t --scale 0.0256 \
    --texture 0=$S/PEASANTM5$T.dtx $M/PEASANTM5.abc $P/source/mm9
done
