#!/bin/bash
# MM9 sources: PEASANTDF1-4.abc with both skins each, and the dwarf female townsfolk clip library
# PEASANTFEMALEDWARF.abc -> source/mm9_lib/pfemaledwarf.glb. Repo root.
set -e
P=level_generation/creatures/mm9_peasantdf_claude
PYG=level_generation/creatures/claude_shared/gltf_venv/bin/python
M=mm9/extracted/MODELS/MODELS
S=mm9/extracted/SKINS/SKINS
for n in 1 2 3 4; do
 for t in a b; do
  T=$(echo $t | tr a-z A-Z)
  PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id pdf$n$t --scale 0.0256 \
    --texture 0=$S/PEASANTDF$n$T.dtx $M/PEASANTDF$n.abc $P/source/mm9
 done
done
PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id pfemaledwarf --scale 0.0256 \
  $M/PEASANTFEMALEDWARF.abc $P/source/mm9_lib
