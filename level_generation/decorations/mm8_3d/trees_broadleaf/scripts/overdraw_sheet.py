#!/usr/bin/env python3
"""review/<id>/overdraw_before_after.png: BEFORE = the v2 row (the lower half of review/<id>/v2_before_after.png:
sprite | LOD0 front | three-quarter | side | LODs) with its layer heat maps (overdraw_v2.png), AFTER = the current
compare + LOD row with its heat maps (overdraw_<tag>.png), each labelled with the mean layers per LOD.
Usage: overdraw_sheet.py <id> <tag>"""
import json, os
from PIL import Image, ImageDraw
import common
spec = common.load(); R = spec['review']; W = spec['work']
tag = common.extra_args()[0]


def label(stats):
    return '  '.join(f"{k.replace('Tree_', '').replace('Tree', 'LOD0')} {v['mean']} (p95 {v['p95']})"
                     for k, v in stats.items())


def row(top, heat, text):
    heat = heat.resize((int(heat.width * top.height / heat.height), top.height))
    r = Image.new('RGB', (top.width + heat.width, top.height + 26), (150, 160, 175))
    r.paste(top, (0, 26)); r.paste(heat, (top.width, 26)); ImageDraw.Draw(r).text((6, 6), text, fill=(0, 0, 0))
    return r


ba = Image.open(os.path.join(R, 'v2_before_after.png')).convert('RGB')
v2_row = ba.crop((0, ba.height // 2, ba.width, ba.height))
a = Image.open(os.path.join(R, 'compare.png')).convert('RGB'); l = Image.open(os.path.join(R, 'lod_consistency.png')).convert('RGB')
l = l.crop((0, 0, l.width, 440)); l = l.resize((int(l.width * a.height / l.height), a.height))
now_row = Image.new('RGB', (a.width + l.width, a.height), (150, 160, 175)); now_row.paste(a, (0, 0)); now_row.paste(l, (a.width, 0))
now_row = now_row.resize((v2_row.width, int(now_row.height * v2_row.width / now_row.width)))
rows = [row(v2_row, Image.open(os.path.join(R, 'overdraw_v2.png')).convert('RGB'),
            'BEFORE (v2) layers per covered pixel: ' + label(json.load(open(os.path.join(W, 'overdraw_v2.json'))))),
        row(now_row, Image.open(os.path.join(R, f'overdraw_{tag}.png')).convert('RGB'),
            'AFTER (inner shell, fewer cards) layers: ' + label(json.load(open(os.path.join(W, f'overdraw_{tag}.json')))))]
w = max(r.width for r in rows)
out = Image.new('RGB', (w, sum(r.height for r in rows)), (150, 160, 175)); y = 0
for r in rows:
    out.paste(r, (0, y)); y += r.height
out.save(os.path.join(R, 'overdraw_before_after.png'))
print('SHEET', os.path.join(R, 'overdraw_before_after.png'))
