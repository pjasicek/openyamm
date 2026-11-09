#!/usr/bin/env python3
"""review/<id>/overdraw_before_after.png: per row (before, after) the review compare sheet and the front-view layer
heat maps of LOD0/1/2 (card fragments in front of the opaque depth: blue 1 layer -> red 8 or more; grey = opaque
covered, no card), with the overdraw numbers. Usage: overdraw_sheet.py <id>"""
import json, os, sys
from PIL import Image, ImageDraw
import common
spec = common.load(); W = spec['work']; R = spec['review']
OD = os.path.join(common.TREES, 'review', 'overdraw')


def row(tag, compare):
    cmp = Image.open(compare).convert('RGB')
    if tag == 'before':          # before_sheet.png = the compare sheet stacked over the LOD sheet: keep its top part
        ref = Image.open(os.path.join(R, 'compare.png'))
        cmp = cmp.crop((0, 0, cmp.width, int(cmp.width * ref.height / ref.width)))
    cmp = cmp.resize((int(cmp.width * 300 / cmp.height), 300))
    heats = [Image.open(os.path.join(OD, f'{tag}_{spec["id"]}_LOD{l}_front.png')).convert('RGB').resize((300, 300))
             for l in (0, 1, 2)]
    r = json.load(open(os.path.join(W, f'overdraw_{tag}.json')))
    img = Image.new('RGB', (cmp.width + 3 * 300, 330), (150, 160, 175)); d = ImageDraw.Draw(img)
    img.paste(cmp, (0, 30))
    for k, h in enumerate(heats):
        img.paste(h, (cmp.width + 300 * k, 30))
        v = [r[f'LOD{k}_{w}'] for w in ('front', 'three_quarter', 'side')]
        d.text((cmp.width + 300 * k + 4, 4), f"LOD{k} layers {sum(x['layers_mean'] for x in v) / 3:.2f}  "
               f"front {sum(x['front_mean'] for x in v) / 3:.2f}", fill=(0, 0, 0))
    d.text((4, 4), tag.upper(), fill=(0, 0, 0))
    return img


before = row('before', os.path.join(R, 'before_sheet.png'))
after = row('after', os.path.join(R, 'compare.png'))
w = max(before.width, after.width)
sheet = Image.new('RGB', (w, before.height + after.height), (150, 160, 175))
sheet.paste(before, (0, 0)); sheet.paste(after, (0, before.height))
sheet.save(os.path.join(R, 'overdraw_before_after.png'))
print('SHEET', os.path.join(R, 'overdraw_before_after.png'))
