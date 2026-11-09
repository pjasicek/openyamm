#!/usr/bin/env python3
"""Before/after sheet of the neck-pass shots (scripts/neck_shots.sh): rows <prefix><tier> for each given prefix and tier, columns
close-up, neck front, neck 3/4, 3/4 head, true profile, low 3/4, party. Args: <out png> <prefixes comma> <tiers comma> (project folder)."""
import sys
from PIL import Image, ImageDraw
out, pre, tiers = sys.argv[1], sys.argv[2].split(','), sys.argv[3].split(',')
V = ['close', 'neckw', 'neckq', 'q34', 'prof', 'low', 'party']; W, H = 420, 318
rows = [(p, t) for t in tiers for p in pre]
S = Image.new('RGB', (W * len(V) + 90, H * len(rows) + 24), (24, 24, 24)); d = ImageDraw.Draw(S)
for c, v in enumerate(V): d.text((90 + c * W + 6, 6), v, fill=(255, 255, 0))
for r, (p, t) in enumerate(rows):
    d.text((6, 24 + r * H + H // 2), f'{p}{t}', fill=(255, 255, 0))
    for c, v in enumerate(V):
        S.paste(Image.open(f'review/shots/{p}{t}_{v}.png').convert('RGB').resize((W, H), Image.LANCZOS), (90 + c * W, 24 + r * H))
S.save(out); print('SHEET', out)
