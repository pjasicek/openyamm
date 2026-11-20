#!/bin/bash
# MM9 sources: PEASANTM1D.abc with both skins (rows 22 M1C, 28 M1D) and the PeasantMale clip library. Repo root.
set -e
P=level_generation/creatures/mm9_peasantm1d_claude
PYG=level_generation/creatures/claude_shared/gltf_venv/bin/python
M=mm9/extracted/MODELS/MODELS
S=mm9/extracted/SKINS/SKINS
for t in c d; do
  T=$(echo $t | tr a-z A-Z)
  PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id pm1d_$t --scale 0.0256 \
    --texture 0=$S/PEASANTM1$T.dtx $M/PEASANTM1D.abc $P/source/mm9
done
