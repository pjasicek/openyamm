#!/bin/bash
# MM9 GIANT.abc at 0.3 x MM9 size (0.0256 * 0.3 = 0.00768: 2.56 m instead of 8.5 m, so the shared scripts' mm/cm constants hold;
# the binding scales by 333.333), one copy per skin with its mallet, then true-handed copies (mirror_glb.py). Repo root.
cd /home/pjasicek/github/OpenYAMM
P=level_generation/creatures/mm9_giant_claude; PYG=$PWD/level_generation/creatures/claude_shared/gltf_venv/bin/python
M=mm9/extracted/MODELS/MODELS; S=mm9/extracted/SKINS/SKINS; C=tools/mm9_import_discovery/convert_abc_model.py
mkdir -p $P/source/true/skins
PYTHONPATH=/usr/lib/python3/dist-packages $PYG $C --id giant2 --scale 0.00768 --texture 0=$S/GIANT2.dtx --texture-id 0=giant2 \
  --texture 1=$S/GIANTMALLET.dtx --texture-id 1=giantmallet $M/GIANT.abc $P/source/t2 | tail -1 | cut -c1-200
PYTHONPATH=/usr/lib/python3/dist-packages $PYG $C --id giant3 --scale 0.00768 --texture 0=$S/GIANT3.dtx --texture-id 0=giant3 \
  --texture 1=$S/YANMIRMALLET.dtx --texture-id 1=yanmirmallet $M/GIANT.abc $P/source/t3 | tail -1 | cut -c1-200
cp $P/source/t2/skins/*.png $P/source/t3/skins/*.png $P/source/true/skins/
for t in 2 3; do python3 $P/scripts/mirror_glb.py $P/source/t$t/giant$t.glb $P/source/true/giant${t}_true.glb; done
