#!/bin/bash
# scripts/qstrip.sh <glb> <name> <clips,comma> [view] : clay strips sheet review/<name>.png (project folder)
G=$1; N=$2; C=$3; V=${4:-q34}
CZ=0.9 F='STRIP' scripts/run.sh src_strips.py $PWD/$G $PWD/review/$N 256 2.4 $V $C > /dev/null
python3 - "$N" "$C" <<'PY'
import sys
from PIL import Image, ImageDraw
n, C = sys.argv[1], sys.argv[2].split(',')
s = 150
o = Image.new('RGB', (6 * s + 110, len(C) * s), (60, 60, 60)); d = ImageDraw.Draw(o)
for r, c in enumerate(C):
    d.text((4, r * s + 60), c, fill=(255, 255, 0))
    for k in range(6):
        o.paste(Image.open(f'review/{n}/{c}_{k}.png').convert('RGB').resize((s, s)), (110 + k * s, r * s))
o.save(f'review/{n}.png')
PY
