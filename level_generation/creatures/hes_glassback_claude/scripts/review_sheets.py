#!/usr/bin/env python3
"""Review sheets from viewer_export.py's Eevee renders: review/tiers_contact.png (quarter, side, front per tier),
review/closeups.png (head, crest, back per tier), review/clips_textured.png (tier B clip frames)."""
import glob, os
from PIL import Image, ImageDraw
R = 'work/renders'
NAMES = {'hgb_a': 'A Glassback Pup (short crest)', 'hgb_b': 'B Glassback (full crest)', 'hgb_c': 'C Glassback Bull (tall crest)'}
for out, views in (('review/tiers_contact.png', ['quarter', 'side', 'front']), ('review/closeups.png', ['head', 'crest', 'back'])):
    W = Image.new('RGB', (2700, 1800), (255, 255, 255)); d = ImageDraw.Draw(W)
    for i, t in enumerate(NAMES):
        for j, v in enumerate(views):
            W.paste(Image.open(f'{R}/{t}_{v}.png'), (900 * i, 600 * j))
        d.text((900 * i + 10, 10), NAMES[t], fill=(255, 255, 255))
    W.resize((1800, 1200)).save(out)
order = ['Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Fidget', 'Death']
files = sorted(glob.glob(f'{R}/clip_*.png'), key=lambda f: (order.index(os.path.basename(f).split('_')[1]), f))
cols = 6; rows = (len(files) + cols - 1) // cols
W = Image.new('RGB', (600 * cols, 420 * rows), (255, 255, 255)); d = ImageDraw.Draw(W)
for k, f in enumerate(files):
    x, y = 600 * (k % cols), 420 * (k // cols); W.paste(Image.open(f), (x, y + 20))
    d.text((x + 6, y + 4), os.path.basename(f)[5:-4] + ' (frame @24 fps)', fill=(0, 0, 0))
W.save('review/clips_textured.png')
