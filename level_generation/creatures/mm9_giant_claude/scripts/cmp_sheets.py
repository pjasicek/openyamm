#!/usr/bin/env python3
"""Review sheets from MM9 renders (references_hd/renders, Blender, MM9's stand pose) and our viewer shots (review/shots, Standing t 0):
review/sheet_mm9_vs_ours.png (per tier: MM9 front, ours front, MM9 back, ours back, MM9 3/4, ours 3/4),
review/sheet_heads.png (per tier: MM9 head front and 3/4, ours front, 3/4, side, back at full shot size crop),
review/sheet_tex.png (texture close-ups per tier: chest, legs, back, mallet), review/sheet_fists.png."""
from PIL import Image, ImageDraw
R = 'references_hd/renders/'; S = 'review/shots/'
def cell(p, size, crop=None):
    im = Image.open(p).convert('RGB')
    if crop: im = im.crop(crop)
    k = min(size[0] / im.width, size[1] / im.height); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    c = Image.new('RGB', size, (40, 40, 46)); c.paste(im, ((size[0] - im.width) // 2, (size[1] - im.height) // 2)); return c
def sheet(rows, size, out, labels):
    s = Image.new('RGB', (size[0] * len(rows[0]), size[1] * len(rows)), (30, 30, 34)); d = ImageDraw.Draw(s)
    for r, row in enumerate(rows):
        for c, (p, crop) in enumerate(row):
            s.paste(cell(p, size, crop), (c * size[0], r * size[1])); d.text((c * size[0] + 6, r * size[1] + 4), labels[r][c], fill=(255, 240, 120))
    s.save(out); print('SHEET', out, s.size)
VC = (180, 0, 856, 763)          # viewer shot crop around the figure
rows, labels = [], []
for t, nm in (('a', 'Plain Giant'), ('b', 'Forest Giant')):
    rows.append([(R + f'stand_{t}_front.png', None), (S + f's{t}_front.png', VC), (R + f'stand_{t}_back.png', None), (S + f's{t}_back.png', VC), (R + f'stand_{t}_q34.png', None), (S + f's{t}_quarter.png', VC)])
    labels.append([f'{nm} MM9 front', 'ours front', 'MM9 back', 'ours back', 'MM9 3/4', 'ours 3/4'])
sheet(rows, (420, 520), 'review/sheet_mm9_vs_ours.png', labels)
HC = (250, 0, 786, 763)
rows, labels = [], []
for t, nm in (('a', 'Plain Giant'), ('b', 'Forest Giant')):
    rows.append([(R + f'standhead_{t}_front.png', None), (R + f'standhead_{t}_q34.png', None), (S + f's{t}_fh.png', HC), (S + f's{t}_qh.png', HC), (S + f's{t}_sh.png', HC), (S + f's{t}_bh.png', HC)])
    labels.append([f'{nm} MM9 head', 'MM9 3/4', 'ours front', 'ours 3/4', 'ours side', 'ours back'])
sheet(rows, (536, 763), 'review/sheet_heads.png', labels)
rows, labels = [], []
for t, nm in (('a', 'Plain Giant'), ('b', 'Forest Giant')):
    rows.append([(S + f's{t}_tex_chest.png', None), (S + f's{t}_tex_legs.png', None), (S + f's{t}_tex_back.png', None), (S + f's{t}_tex_mallet.png', None)])
    labels.append([f'{nm} chest', 'legs', 'back', 'mallet'])
sheet(rows, (700, 515), 'review/sheet_tex.png', labels)
rows, labels = [], []
for t, nm in (('a', 'Plain Giant'), ('b', 'Forest Giant')):
    rows.append([(S + f's{t}_fist.png', None), (S + f's{t}_fist2.png', None)])
    labels.append([f'{nm} fists, Standing', 'AttackMelee 0.3 s'])
sheet(rows, (900, 662), 'review/sheet_fists.png', labels)
