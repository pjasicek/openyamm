#!/bin/bash
# MM9 sources: PEASANTDM3.abc with both skins (row 11 Town PEASANTDM3B, row 12 Shopkeeper PEASANTDM3A)
# and the dwarf male townsfolk clip library PEASANTMALEDWARF.abc -> source/mm9_lib/pmaledwarf.glb. Repo root.
set -e
P=level_generation/creatures/mm9_peasantdm3_claude
PYG=level_generation/creatures/claude_shared/gltf_venv/bin/python
M=mm9/extracted/MODELS/MODELS
S=mm9/extracted/SKINS/SKINS
for t in a b; do
  T=$(echo $t | tr a-z A-Z)
  PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id pdm3$t --scale 0.0256 \
    --texture 0=$S/PEASANTDM3$T.dtx $M/PEASANTDM3.abc $P/source/mm9
done
PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id pmaledwarf --scale 0.0256 \
  $M/PEASANTMALEDWARF.abc $P/source/mm9_lib
