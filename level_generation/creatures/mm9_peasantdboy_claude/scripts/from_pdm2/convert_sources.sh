#!/bin/bash
# MM9 sources: PEASANTDM2.abc with both skins (row 9 PEASANTDM2A; PEASANTDM2B unused by any row, kept as tier B)
# and the dwarf male townsfolk clip library PEASANTMALEDWARF.abc -> source/mm9_lib/pmaledwarf.glb. Repo root.
set -e
P=level_generation/creatures/mm9_peasantdm2_claude
PYG=level_generation/creatures/claude_shared/gltf_venv/bin/python
M=mm9/extracted/MODELS/MODELS
S=mm9/extracted/SKINS/SKINS
for t in a b; do
  T=$(echo $t | tr a-z A-Z)
  PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id pdm2$t --scale 0.0256 \
    --texture 0=$S/PEASANTDM2$T.dtx $M/PEASANTDM2.abc $P/source/mm9
done
PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id pmaledwarf --scale 0.0256 \
  $M/PEASANTMALEDWARF.abc $P/source/mm9_lib
