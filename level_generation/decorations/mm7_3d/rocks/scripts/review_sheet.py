#!/usr/bin/env python3
"""Review sheet for one rock: x2 sprite | LOD0 at the sprite's view | turntable (+90/180/270) | LOD1..3, with triangle
counts; prints the mean colour of the sprite and of the LOD0 render (opaque pixels, and lit: above the median luma). With --calibrate, scales the
grade gain in rocks.json by linear(sprite lit mean) / linear(render lit mean) (lit: pixels above the median luma; rocks.json `calibrate: mid` uses the midpoint of the mean and the lit colour) (run build_rock.py --regrade after).
Usage: review_sheet.py <rock> [--calibrate]"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
import scans

rock = sys.argv[1]
cfgs = json.load(open(os.path.join(scans.HERE, 'rocks.json'))); cfg = cfgs[rock]
R = os.path.join(scans.HERE, 'work', rock, 'review')
tris = cfg['targets']


def crop(im):
    im = im.convert('RGBA'); return im.crop(im.getchannel('A').point(lambda a: 255 if a > 8 else 0).getbbox())


def mean(im, upper=False):
    """Mean colour of the opaque pixels; upper: of those above the median luma (the lit faces)."""
    a = np.asarray(im.convert('RGBA'), np.float32) / 255; c = a[..., :3][a[..., 3] > 0.5]
    if upper:
        luma = c @ np.array([0.2126, 0.7152, 0.0722]); c = c[luma >= np.median(luma)]
    return c.mean(0) * 255


sprite = Image.open(os.path.join(scans.X2, rock + '_p2.png'))
items = [(f'{rock} sprite (x2)', sprite), (f"LOD0 yaw {cfg['review_yaw']}", Image.open(os.path.join(R, 'render_lod0.png')))]
items += [(f'turntable +{y}', Image.open(os.path.join(R, f'render_yaw{y:03d}.png'))) for y in (90, 180, 270)]
items += [(f'LOD{i}  {tris[i]} tris', Image.open(os.path.join(R, f'render_lod{i}.png'))) for i in (1, 2, 3)]
W, H = 300, 260
sheet = Image.new('RGB', (W * len(items), H + 26), (88, 104, 88)); d = ImageDraw.Draw(sheet)
for i, (label, im) in enumerate(items):
    im = crop(im); f = min((W - 12) / im.width, (H - 8) / im.height)
    im = im.resize((max(1, int(im.width * f)), max(1, int(im.height * f))), Image.LANCZOS)
    sheet.paste(im, (i * W + (W - im.width) // 2, 26 + H - 4 - im.height), im)
    d.text((i * W + 6, 6), label, fill=(255, 255, 255))
path = os.path.join(R, f'{rock}_review.png'); sheet.save(path); print('SHEET', path)
render = Image.open(os.path.join(R, 'render_lod0.png'))
print('MEAN sprite', mean(sprite).round(1), 'render', mean(render).round(1))
ms, mr = mean(sprite, True), mean(render, True)
print('LIT sprite', ms.round(1), 'render', mr.round(1))
if cfg.get('calibrate') == 'mid':
    # calibrate on the midpoint of the overall mean and the lit-face colour (a darker, less pale result)
    ms, mr = (ms + mean(sprite)) / 2, (mr + mean(render)) / 2
    print('MID sprite', ms.round(1), 'render', mr.round(1))
if '--calibrate' in sys.argv:
    lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    ratio = lin(ms / 255) / lin(mr / 255)
    cfg['grade']['gain'] = [round(float(g * r), 3) for g, r in zip(cfg['grade']['gain'], ratio)]
    json.dump(cfgs, open(os.path.join(scans.HERE, 'rocks.json'), 'w'), indent=2)
    print('CALIBRATED gain', cfg['grade']['gain'])
