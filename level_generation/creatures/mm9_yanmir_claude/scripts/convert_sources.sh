#!/bin/bash
# MM9 YANMIR.abc at 0.3 x MM9 size (0.0256 * 0.3 = 0.00768, as mm9_giant_claude: about 2.6 m instead of 8.6 m, so the
# shared scripts' mm/cm constants hold; the binding scales by 333.333), then the true-handed copy (mirror_glb.py). Repo root.
# The staff is a piece of YANMIR.abc on the body skin (material 0); YANMIRMALLET.dtx belongs to the Forest Giant.
cd /home/pjasicek/github/OpenYAMM
P=level_generation/creatures/mm9_yanmir_claude; PYG=$PWD/level_generation/creatures/claude_shared/gltf_venv/bin/python
M=mm9/extracted/MODELS/MODELS; S=mm9/extracted/SKINS/SKINS; C=tools/mm9_import_discovery/convert_abc_model.py
mkdir -p $P/source/true/skins
PYTHONPATH=/usr/lib/python3/dist-packages $PYG $C --id yanmir --scale 0.00768 --texture 0=$S/YANMIR.dtx --texture-id 0=yanmir \
  $M/YANMIR.abc $P/source/raw | tail -1 | cut -c1-200
cp $P/source/raw/skins/*.png $P/source/true/skins/
python3 $P/scripts/mirror_glb.py $P/source/raw/yanmir.glb $P/source/true/yanmir_true.glb
