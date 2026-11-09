#!/bin/bash
# MM9 sources at metre scale for the three Horde rows, then true-handed copies (mirror_glb.py). Repo root.
cd /home/pjasicek/github/OpenYAMM
P=level_generation/creatures/mm9_clansoldier_claude; PYG=$PWD/level_generation/creatures/claude_shared/gltf_venv/bin/python
M=mm9/extracted/MODELS/MODELS; S=mm9/extracted/SKINS/SKINS
i=0
for t in "1 BELDONIAN1 BELDSWORD BELDSHIELD1" "2 BELDONIAN2 BELDSWORD BELDSHIELD2" "3 BELDONIAN3 BELDSWORDOLD BELDSHIELD3"; do
  set -- $t
  PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id clan$1 --scale 0.0256 \
    --texture 0=$S/$2.dtx --texture-id 0=${2,,} --texture 1=$S/$3.dtx --texture-id 1=${3,,} --texture 2=$S/$4.dtx --texture-id 2=${4,,} \
    $M/CLANSOLDIER.abc $P/source/c$1 | tail -1 | cut -c1-160
  python3 $P/scripts/mirror_glb.py $P/source/c$1/clan$1.glb $P/source/true/clan$1_true.glb
done
