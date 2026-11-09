#!/bin/bash
# MM9 sources: PEASANTHOF1.abc with skins A and B (rows 61/62 A, 63 B), PEASANTHOF1 with skin C (for comparison only),
# PEASANTHOF2.abc with skin C (row 64), and the half-orc female clip library PEASANTHOFEMALE.abc. Repo root.
set -e
P=level_generation/creatures/mm9_peasanthof_claude
PYG=level_generation/creatures/claude_shared/gltf_venv/bin/python
M=mm9/extracted/MODELS/MODELS
S=mm9/extracted/SKINS/SKINS
for t in a b c; do
  T=$(echo $t | tr a-z A-Z)
  PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id phof1$t --scale 0.0256 \
    --texture 0=$S/PEASANTHOF1$T.dtx $M/PEASANTHOF1.abc $P/source/mm9
done
PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id phof2c --scale 0.0256 \
  --texture 0=$S/PEASANTHOF1C.dtx $M/PEASANTHOF2.abc $P/source/mm9
PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id phofemale --scale 0.0256 \
  $M/PEASANTHOFEMALE.abc $P/source/mm9_lib
