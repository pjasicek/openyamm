#!/usr/bin/env python3
"""Review sheets for one palm from render_review.py output in work/<id>/:
review/<id>/compare.png (sprite | LOD0 front | three-quarter | back, on grey, bottom-aligned at the same scale as
the sprite's height) and review/<id>/lods.png (every level from the front with triangle counts, mean colour of
opaque pixels and coverage relative to LOD0, plus the sprite's mean). Prints the stats and writes
work/<id>/lod_stats.json. Usage: sheet.py <id> <tri0> <tri1> <tri2> <tri3>"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palm_common as dc
sid, tris = sys.argv[1], sys.argv[2:6]
W, R = dc.work(sid), dc.review(sid)
T = 420
GREY = (128, 138, 155, 255)


def crop(im):
    im = im.convert('RGBA'); box = im.getbbox() or (0, 0, im.width, im.height)
    return im.crop(box)


def tile(im, height=None, size=T):
    s = (size * 0.94) / max(im.size) if height is None else height
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    bg = Image.new('RGBA', (size, size), GREY); bg.alpha_composite(im, ((size - im.width) // 2, size - im.height - 4))
    return bg.convert('RGB')


def stats(im):
    x = np.asarray(im.convert('RGBA')).astype(float); m = x[..., 3] > 128
    return x[m][:, :3].mean(0).round(1).tolist(), int(m.sum())


sprite = crop(Image.open(os.path.join(dc.SPRITES, dc.SPECIES[sid]['sprite'])))
renders = {v: Image.open(os.path.join(W, f'rv_Plant_{v}.png')).convert('RGBA') for v in ('front', 'three_quarter', 'back')}
front = crop(renders['front'])
# scale: the sprite and the front render share one height in the tile
scale_s = (T * 0.94) / max(sprite.size)
sprite_h = sprite.height * scale_s
scale_r = sprite_h / front.height
tiles = [tile(sprite, scale_s)] + [tile(crop(renders[v]), scale_r) for v in ('front', 'three_quarter', 'back')]
sheet = Image.new('RGB', (T * 4, T + 22), 'white'); d = ImageDraw.Draw(sheet)
for i, (t, label) in enumerate(zip(tiles, ('sprite', 'LOD0 front', 'LOD0 three-quarter', 'LOD0 back'))):
    sheet.paste(t, (i * T, 22)); d.text((i * T + 4, 5), label, fill='black')
sheet.save(os.path.join(R, 'compare.png'))
# LOD row
names = ['Plant', 'Plant_LOD1', 'Plant_LOD2', 'Plant_LOD3']
st = {}
ims = []
for n in names:
    im = Image.open(os.path.join(W, f'lc_{n}_front.png')).convert('RGBA')
    st[n] = dict(zip(('mean_rgb', 'opaque_px'), stats(im))); ims.append(im)
for a, b in zip(names, names[1:]):
    st[b]['mean_diff_vs_previous'] = np.abs(np.subtract(st[a]['mean_rgb'], st[b]['mean_rgb'])).round(1).tolist()
    st[b]['coverage_vs_previous'] = round(st[b]['opaque_px'] / st[a]['opaque_px'] - 1, 3)
sm = stats(sprite)[0]
st['sprite_mean_rgb'] = sm
json.dump(st, open(os.path.join(W, 'lod_stats.json'), 'w'), indent=1)
w0 = ims[0].width
sheet = Image.new('RGB', (w0 * 4, ims[0].height + 40), 'white'); d = ImageDraw.Draw(sheet)
for k, (n, im) in enumerate(zip(names, ims)):
    bg = Image.new('RGBA', im.size, GREY); bg.alpha_composite(im); sheet.paste(bg.convert('RGB'), (k * w0, 40))
    s = st[n]
    d.text((k * w0 + 4, 3), f'{n}: {tris[k]} tris', fill='black')
    d.text((k * w0 + 4, 20), f'mean {s["mean_rgb"]} cov {s.get("coverage_vs_previous", 0):+.3f}', fill='black')
sheet.save(os.path.join(R, 'lods.png'))
for n in names:
    print(n, st[n])
print('sprite mean', sm)
