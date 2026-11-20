#!/bin/bash
# MM9 sources: FRE.abc with its skin Fre.dtx (row 256), the statue skin FRESCULPT (Hall of the Gods prop, reference only),
# and the PeasantF1/F3/F4 models it was compared with. Repo root.
set -e
P=level_generation/creatures/mm9_fre_claude
PYG=level_generation/creatures/claude_shared/gltf_venv/bin/python
M=mm9/extracted/MODELS/MODELS
S=mm9/extracted/SKINS/SKINS
conv() { PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --scale 0.0256 "$@"; }
conv --id fre --texture $S/FRE.dtx $M/FRE.abc $P/source/mm9
conv --id fre_sculpt --texture $S/FRESCULPT.dtx $M/FRE.abc $P/source/mm9_sculpt
conv --id pf1b --texture $S/PEASANTF1B.dtx $M/PEASANTF1.abc $P/source/mm9_cmp
conv --id pf3a --texture $S/PEASANTF3A.dtx $M/PEASANTF3.abc $P/source/mm9_cmp
conv --id pf4a --texture $S/PEASANTF4A.dtx $M/PEASANTF4.abc $P/source/mm9_cmp
