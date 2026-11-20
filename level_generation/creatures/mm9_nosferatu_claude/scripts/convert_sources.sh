#!/bin/bash
# MM9 sources at metre scale, then true-handed copies (mirror_glb.py).
cd /home/pjasicek/github/OpenYAMM
P=level_generation/creatures/mm9_nosferatu_claude
. $P/scripts/env.sh
for n in 1 2 3; do
  PYTHONPATH=/usr/lib/python3/dist-packages $PYG tools/mm9_import_discovery/convert_abc_model.py --id nosferatu$n --scale 0.0256 \
    --texture 0=mm9/extracted/SKINS/SKINS/NOSFERATU$n.dtx --texture-id 0=nosferatu$n mm9/extracted/MODELS/MODELS/NOSFERATU.abc $P/source/n$n | tail -1 | cut -c1-200
  python3 $P/scripts/mirror_glb.py $P/source/n$n/nosferatu$n.glb $P/source/n$n/nosferatu${n}_true.glb
  python3 $P/scripts/rename_bones.py $P/source/n$n/nosferatu${n}_true.glb $P/source/n$n/n${n}.glb
done
