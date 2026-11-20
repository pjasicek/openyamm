#!/bin/bash
# MM9 reference renders of PEASANTHOM2 with skin PEASANTHOM2A, composed like mm9_peasanthom1_claude's references_hd/mm9_*_a.png
# (five body views 640 px: q34 front left back right; five head views 512 px: front left q34 right back; skin x4). Repo root.
set -e
P=level_generation/creatures/mm9_peasanthom2_claude
R=$P/review/mm9
blender -b --python $P/scripts/ref_renders.py -- $P/source/mm9/phom2_a.glb $R h2 640 2.4 > /dev/null 2>&1
CENTER=0,0,0.93 VIEWS=front,left,q34,right,back blender -b --python $P/scripts/ref_renders.py -- $P/source/mm9/phom2_a.glb $R head_h2 512 0.55 > /dev/null 2>&1
python3 - "$R" "$P" <<'PY'
import sys
from PIL import Image
R, P = sys.argv[1:]
def row(names, size):
    o = Image.new('RGB', (size * len(names), size))
    for i, n in enumerate(names):
        o.paste(Image.open(f'{R}/{n}.png').convert('RGB').resize((size, size)), (i * size, 0))
    return o
row([f'h2_{v}' for v in ('q34', 'front', 'left', 'back', 'right')], 640).save(f'{P}/references_hd/mm9_views_h2.png')
row([f'head_h2_{v}' for v in ('front', 'left', 'q34', 'right', 'back')], 512).save(f'{P}/references_hd/mm9_head_views_h2.png')
Image.open(f'{P}/source/mm9/skins/phom2_a.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(f'{P}/references_hd/mm9_skin_x4_h2.png')
PY
