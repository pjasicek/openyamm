#!/usr/bin/env python3
"""Before/after review sheet of the 2026-10-30 head/jaw/fly rework from work/rev/ renders (review_renders.py) and
review/fly_head_height_20261030.png. Writes review/headjaw_rework_20261030.png."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE = Path(__file__).resolve().parents[2]; R = HERE / 'work' / 'rev'
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
FS = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
W = 2400
rows = []


def row(title, cells, h):
    w = W // len(cells)
    im = Image.new('RGB', (W, h + 40), (30, 30, 32)); d = ImageDraw.Draw(im)
    d.text((10, 8), title, fill=(240, 240, 235), font=F)
    for i, (f, cap) in enumerate(cells):
        t = Image.open(R / f).convert('RGB'); t.thumbnail((w, h))
        im.paste(t, (i * w + (w - t.width) // 2, 40))
        d.text((i * w + 8, 44), cap, fill=(255, 255, 255), font=FS)
    rows.append(im)


row('41.png framing: head, Standing (mouth closed). Before: face, frills, horns in the 2K body atlas. After: own head set + real mouth',
    [('before_stand_f41.png', 'before'), ('after_stand_f41.png', 'after'), ('before_stand_f42.png', 'before'), ('after_stand_f42.png', 'after')], 600)
row('42.png framing: Fidget frame 36 at 48 fps (0.75 s), mouth wide open. Before: lip curtain. After: cavity with gums, palate, tongue, throat',
    [('before_fid36_f42.png', 'before'), ('after_fid36_f42.png', 'after'), ('before_fid36_low.png', 'before (into the mouth)'), ('after_fid36_low.png', 'after (into the mouth)')], 600)
EX = [('Cast_1_0', 'Cast 1.0 s (41 deg)'), ('Death_1_167', 'Death 1.17 s (44.5 deg, widest)'), ('AttackRanged_0_433', 'AttackRanged 0.43 s (33 deg)'),
      ('Taunt_0_867', 'Taunt 0.87 s'), ('Hit_0_6', 'Hit 0.6 s'), ('Land_0_867', 'Land 0.87 s (33 deg)')]
row('Other mouth-open extremes, BEFORE (side)', [(f'before_{k}_f42.png', c) for k, c in EX], 400)
row('Other mouth-open extremes, AFTER (side)', [(f'after_{k}_f42.png', c) for k, c in EX], 400)
row('Other mouth-open extremes, AFTER (into the mouth from the front, below)', [(f'after_{k}_low.png', c) for k, c in EX], 400)
row('Shading close-up, clay (no textures): flat-shaded original vs now (smooth, hard edges only at creases > 60 deg and the lips)',
    [('flat_clay_f41.png', 'flat original'), ('after_clay_f41.png', 'now'), ('flat_clay_f42.png', 'flat original'), ('after_clay_f42.png', 'now')], 600)
fly = Image.open(HERE / 'review' / 'fly_head_height_20261030.png').convert('RGB'); fly.thumbnail((W, 700))
fr = Image.new('RGB', (W, fly.height + 40), (30, 30, 32)); ImageDraw.Draw(fr).text((10, 8), 'Fly loop head height: before (per-key floor raise driven by the wing tips) vs after (one constant lift) vs MM9', fill=(240, 240, 235), font=F)
fr.paste(fly, ((W - fly.width) // 2, 40)); rows.append(fr)
out = Image.new('RGB', (W, sum(r.height for r in rows)), (30, 30, 32)); y = 0
for r in rows:
    out.paste(r, (0, y)); y += r.height
out.save(HERE / 'review' / 'headjaw_rework_20261030.png')
small = out.copy(); small.thumbnail((1400, 4000)); small.save(HERE / 'work' / 'rev' / 'sheet_small.png')
print('SHEET', out.size)
