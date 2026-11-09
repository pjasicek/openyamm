#!/bin/bash
# MM9 source at metre scale, then a true-handed copy (mirror_glb.py). One skin carries all three rows. Repo root.
cd /home/pjasicek/github/OpenYAMM
P=level_generation/creatures/mm9_dwarf_claude; PYG=$PWD/level_generation/creatures/claude_shared/gltf_venv/bin/python
M=mm9/extracted/MODELS/MODELS; S=mm9/extracted/SKINS/SKINS
mkdir -p $P/source/true $P/source/axe
PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id dwarf --scale 0.0256 \
  --texture 0=$S/DWARF.dtx --texture-id 0=dwarf $M/DWARF.abc $P/source/d1 | tail -1 | cut -c1-200
python3 $P/scripts/mirror_glb.py $P/source/d1/dwarf.glb $P/source/true/dwarf_true.glb
