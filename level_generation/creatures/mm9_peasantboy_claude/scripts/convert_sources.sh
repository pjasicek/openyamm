#!/bin/bash
# MM9 sources for the human boy family: PEASANTBOY1 (row 69 skin PEASANTBOY1), PEASANTBOY2 (row 70 skin PEASANTBOY3),
# PEASANTBOY1E (row 73 skin PEASANTBOY2), each with its row's skin, plus the child clip library PEASANTCHILDBOY.abc.
# Repo root.
set -e
P=level_generation/creatures/mm9_peasantboy_claude
PYG=level_generation/creatures/claude_shared/gltf_venv/bin/python
M=mm9/extracted/MODELS/MODELS
S=mm9/extracted/SKINS/SKINS
conv() { PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py "$@"; }
conv --id pboy1 --scale 0.0256 --texture 0=$S/PEASANTBOY1.dtx $M/PEASANTBOY1.abc $P/source/mm9
conv --id pboy2 --scale 0.0256 --texture 0=$S/PEASANTBOY3.dtx $M/PEASANTBOY2.abc $P/source/mm9
conv --id pboy1e --scale 0.0256 --texture 0=$S/PEASANTBOY2.dtx $M/PEASANTBOY1E.abc $P/source/mm9
conv --id pchildboy --scale 0.0256 $M/PEASANTCHILDBOY.abc $P/source/mm9_lib
