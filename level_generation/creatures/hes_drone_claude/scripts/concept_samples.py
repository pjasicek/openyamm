#!/usr/bin/env python3
"""Median sRGB colour of hand-placed boxes on the approved concept sheet (references_hd/concept.png, 1536x1024):
tier A = the large view, B = upper-left view, C = middle-left view. Writes work/concept_samples.json and
review/tex/concept_samples.png (boxes drawn) so the boxes can be checked."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[1]
BOXES = {   # tier: region: [x0, y0, x1, y1]
    'A': {'casing': [[930, 300, 1010, 360], [1350, 420, 1400, 480]], 'resin': [[1180, 250, 1215, 280], [1250, 440, 1275, 470]],
          'trim': [[840, 300, 860, 350]], 'glow': [[740, 415, 770, 445]], 'bone': [[1180, 175, 1200, 215]]},
    'B': {'casing': [[290, 100, 340, 150], [490, 120, 530, 160]], 'resin': [[380, 165, 400, 185], [430, 210, 450, 230]],
          'trim': [[250, 120, 262, 160]], 'glow': [[195, 135, 210, 150]], 'bone': [[370, 45, 385, 70]]},
    'C': {'casing': [[220, 395, 280, 450], [470, 450, 510, 490]], 'resin': [[380, 400, 400, 420], [380, 480, 400, 500]],
          'trim': [[240, 480, 330, 488], [120, 360, 150, 372]], 'glow': [[105, 470, 125, 490]], 'bone': [[380, 380, 395, 405]]},
}
im = Image.open(ROOT / 'references_hd' / 'concept.png').convert('RGB'); a = np.asarray(im).astype(float)
out = {}
d = ImageDraw.Draw(im)
for tier, regions in BOXES.items():
    out[tier] = {}
    for region, boxes in regions.items():
        px = np.concatenate([a[y0:y1, x0:x1].reshape(-1, 3) for x0, y0, x1, y1 in boxes])
        lum = px @ [0.2126, 0.7152, 0.0722]
        out[tier][region] = {'median': np.median(px, 0).round(1).tolist(),
                             'p10': px[lum <= np.percentile(lum, 10)].mean(0).round(1).tolist(),
                             'p90': px[lum >= np.percentile(lum, 90)].mean(0).round(1).tolist()}
        for b in boxes:
            d.rectangle(b, outline=(0, 255, 0)); d.text((b[0], b[1] - 10), f'{tier}{region[0]}', fill=(0, 255, 0))
        print(tier, region, out[tier][region])
json.dump(out, open(ROOT / 'work' / 'concept_samples.json', 'w'), indent=1)
(ROOT / 'review' / 'tex').mkdir(parents=True, exist_ok=True); im.save(ROOT / 'review' / 'tex' / 'concept_samples.png')
