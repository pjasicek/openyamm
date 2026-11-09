#!/bin/bash
# Back faces magenta (what the one-sided viewer culls) after the cut, PeasantF4's diag_posed_pf4.py (read only), installed and a
# candidate: back, low back, elbows from behind (level and low), chest front; Standing, Fidget 1.0 s, Hit 0.7 s. One Blender.
# Then one sheet per view set (installed row above candidate row). Usage (project folder): scripts/diag_backfaces.sh <candidate glb> <tag>
set -euo pipefail
C=$1; TAG=$2; O=review/diag_backfaces; mkdir -p $O
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
V="back=0,2.5,1.0/0,0,1.0/1.9;lowback=0,1.2,0.45/0,0,1.05/0.9;eL=-0.6,1.0,1.1/-0.22,0,1.05/0.55;eR=0.6,1.0,1.1/0.22,0,1.05/0.55;eLlow=-0.5,0.9,0.55/-0.22,0,1.05/0.55;eRlow=0.5,0.9,0.55/0.22,0,1.05/0.55;chest=0,-1.5,1.2/0,0,1.18/0.6"
for g in "before/mm9_peasantf4.glb:inst" "$C:$TAG"; do
  $BL --python ../mm9_peasantf4_claude/scripts/diag_posed_pf4.py -- "$PWD/${g%%:*}" "$PWD/$O/${g##*:}" "Standing:0,Fidget:1.0,Hit:0.7" "$V" 500 2>&1 | grep -E "POSED|Error|Trace" || true
done
python3 - "$TAG" <<'PY'
import sys
from PIL import Image, ImageDraw
tag = sys.argv[1]; O = 'review/diag_backfaces'
views = ['back', 'lowback', 'eL', 'eR', 'eLlow', 'eRlow', 'chest']
for clip in ('Standing0', 'Fidget1.0', 'Hit0.7'):
    W = 300; sh = Image.new('RGB', (W * len(views), (W + 18) * 2), (25, 25, 25)); d = ImageDraw.Draw(sh)
    for r, k in enumerate(('inst', tag)):
        for i, v in enumerate(views):
            sh.paste(Image.open(f'{O}/{k}_{clip}_{v}.png').convert('RGB').resize((W, W)), (i * W, r * (W + 18) + 18))
            d.text((i * W + 4, r * (W + 18) + 3), f'{k} {clip} {v}', fill=(255, 220, 120))
    sh.save(f'{O}/sheet_{tag}_{clip}.png'); print('SHEET', f'{O}/sheet_{tag}_{clip}.png')
PY
