#!/bin/bash
# MM9 sources: KROHN.abc with its three material skins (0 body+head KROHN, 1 sword KROHNSWORD, 2 spear KROHNSPEAR)
# and the statue's sculpt skins. Repo root.
set -e
P=level_generation/creatures/mm9_krohn_claude
PYG=level_generation/creatures/claude_shared/gltf_venv/bin/python
M=mm9/extracted/MODELS/MODELS
S=mm9/extracted/SKINS/SKINS
PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id krohn --scale 0.0256 \
  --texture 0=$S/KROHN.dtx --texture 1=$S/KROHNSWORD.dtx --texture 2=$S/KROHNSPEAR.dtx $M/KROHN.abc $P/source/mm9
PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id krohn_sculpt --scale 0.0256 \
  --texture 0=$S/KROHNSCULPT.dtx --texture 1=$S/KROHNSWORDSCULPT.dtx --texture 2=$S/KROHNSPEARSCULPT.dtx $M/KROHN.abc $P/source/mm9_sculpt
