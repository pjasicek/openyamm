#!/usr/bin/env python3
"""Concept vs model comparison: per turret one row of pairs, concept crop beside the v2 render from the same side
(main three-quarter, side, back), plus the v1 hand-built model's rest render. Writes review/concept_vs_model.png."""
import os
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = 420


def fit(path, label, bg=(30, 30, 30)):
    im = Image.open(path).convert('RGBA'); w = int(im.width * H / im.height)
    tile = Image.new('RGB', (w, H), bg); tile.paste(im.resize((w, H)), (0, 0), im.resize((w, H)))
    ImageDraw.Draw(tile).rectangle((0, 0, 8 + 7 * len(label), 18), fill=(0, 0, 0))
    ImageDraw.Draw(tile).text((4, 3), label, fill=(255, 230, 80))
    return tile


rows = []
for n in ('ward_turret', 'gate_bastion'):
    r = os.path.join(HERE, 'references_hd', n)
    v = os.path.join(HERE, 'review', f'hes_{n}_actor')
    tiles = [fit(f'{r}/concept_main.png', 'concept main'), fit(f'{v}_rest.png', 'v2 Meshy (rest, concept side)'),
             fit(f'{r}/concept_side.png', 'concept side'), fit(f'{v}_side.png', 'v2 side'),
             fit(f'{r}/concept_back.png', 'concept back'), fit(f'{v}_back_straight.png' if n == 'ward_turret' else f'{v}_back.png', 'v2 back'),
             fit(os.path.join(HERE, 'v1_hand_built', 'review', f'hes_{n}_actor_rest.png'), 'v1 hand-built (replaced)')]
    row = Image.new('RGB', (sum(t.width for t in tiles) + 6 * len(tiles), H), (20, 20, 20)); x = 0
    for t in tiles:
        row.paste(t, (x, 0)); x += t.width + 6
    rows.append(row)
W = max(r.width for r in rows)
sheet = Image.new('RGB', (W, H * len(rows) + 6), (20, 20, 20))
for i, r in enumerate(rows):
    sheet.paste(r, (0, i * (H + 6)))
out = os.path.join(HERE, 'review', 'concept_vs_model.png')
sheet.save(out); print('SHEET', out, sheet.size)
