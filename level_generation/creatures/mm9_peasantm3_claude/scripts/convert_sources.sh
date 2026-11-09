#!/bin/bash
# MM9 sources: PEASANTM3.abc with both skins (row 51 PEASANTM3B, row 53 PEASANTM3A). Repo root.
# The PeasantMale clip library source/mm9_lib/pmale.glb is copied from mm9_peasantm1_claude (same 45-joint skeleton).
set -e
P=level_generation/creatures/mm9_peasantm3_claude
PYG=level_generation/creatures/claude_shared/gltf_venv/bin/python
M=mm9/extracted/MODELS/MODELS
S=mm9/extracted/SKINS/SKINS
for t in a b; do
  T=$(echo $t | tr a-z A-Z)
  PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id pm3$t --scale 0.0256 \
    --texture 0=$S/PEASANTM3$T.dtx $M/PEASANTM3.abc $P/source/mm9
done
