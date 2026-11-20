#!/bin/bash
# MM9 vs ours full-body sheet in the review viewer's lighting (Standing, front / 3/4 / left / back, both tiers).
# Usage (repo root): level_generation/creatures/mm9_peasantf4_claude/scripts/vs_sheet_pf4.sh <rev> -> review/sheet_mm9_vs_ours_<rev>.png
set -euo pipefail
P=level_generation/creatures/mm9_peasantf4_claude; R=$1
for t in a b; do SHA=$(python3 -c "import json;m=json.load(open('$P/review/viewer/manifest.json'));print(next(x['sha256'] for x in m['models'] if x['id']=='pf4_$t'))"); H=$(python3 -c "import json,urllib.parse;print(urllib.parse.quote(json.dumps({'clip':'Standing','model_sha256':'$SHA'})))"); MODEL_SHA=$SHA timeout 300 node $P/scripts/viewer_shots_pf4.mjs "http://127.0.0.1:8912/$P/review/viewer/#$H" $P/review/shots pf4_${t}_${R}f:Standing:0:front:body pf4_${t}_${R}q:Standing:0:quarter:body pf4_${t}_${R}l:Standing:0:left:body pf4_${t}_${R}b:Standing:0:back:body | tail -1; done
cd $P && R=$R python3 - <<'PY'
import os
from PIL import Image, ImageDraw
R = os.environ['R']; C = 420
def sq(p, crop=None):
    im = Image.open(p).convert('RGB')
    if crop: im = im.crop(crop)
    w, h = im.size; c = min(w, h); im = im.crop(((w - c) // 2, (h - c) // 2, (w - c) // 2 + c, (h - c) // 2 + c)); return im.resize((C, C), Image.LANCZOS)
rows = []
for t in 'ab':
    rows.append((f'MM9 F4{t}', [sq(f'review/mm9/full/pf4{t}_{v}.png') for v in ('front', 'q34', 'left', 'back')]))
    rows.append((f'ours pf4_{t} {R} (viewer)', [sq(f'review/shots/pf4_{t}_{R}{v}.png', (268, 60, 768, 763)) for v in 'fqlb']))
S = Image.new('RGB', (4 * C, len(rows) * C), (30, 30, 30)); d = ImageDraw.Draw(S)
for r, (lab, ims) in enumerate(rows):
    for c, im in enumerate(ims): S.paste(im, (c * C, r * C))
    d.text((6, r * C + 6), lab, fill=(255, 255, 0))
S.save(f'review/sheet_mm9_vs_ours_{R}.png'); print('VS sheet', R)
PY
