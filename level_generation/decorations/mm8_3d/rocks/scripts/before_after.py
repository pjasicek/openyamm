#!/usr/bin/env python3
"""Before/after sheet of the native shading pass: one row per rock (native x2 sprite | before, neutral light | after,
neutral light | after, top-lit), with the mean sRGB and luminance spread (p10..p90) of each image's opaque pixels.
Usage: before_after.py out.png rock..."""
import glob, json, os, sys
import numpy as np
from PIL import Image, ImageDraw


def sprite_path(name):
    """A native x2 sprite: the runtime copy, else the 2026-10-16 retirement archive (read only)."""
    live = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2', name)
    return live if os.path.exists(live) else os.path.join(REPO, 'assets_legacy', 'decorations_x2_mm8_20261016', name)


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
INV = {e['name']: e for e in json.load(open(os.path.join(HERE, '..', 'inventory.json')))}
out, *rocks = sys.argv[1:]
T = 260


def stats(im):
    a = np.asarray(im.convert('RGBA')).astype(float); m = a[..., 3] > 128
    rgb = a[m][:, :3]; lum = rgb @ [0.2126, 0.7152, 0.0722]
    return f'mean {tuple(int(v) for v in rgb.mean(0))} lum {int(np.percentile(lum, 10))}-{int(np.percentile(lum, 90))}'


def tile(path):
    im = Image.open(path).convert('RGBA'); im = im.crop(im.getbbox()); s = T * 0.9 / max(im.size)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    c = Image.new('RGBA', (T, T), (96, 100, 110, 255)); c.alpha_composite(im, ((T - im.width) // 2, T - im.height - 4))
    return c.convert('RGB'), stats(Image.open(path))


sheet = Image.new('RGB', (T * 4, (T + 34) * len(rocks)), (255, 255, 255)); d = ImageDraw.Draw(sheet)
for r, rock in enumerate(rocks):
    R = os.path.join(HERE, 'review', rock)
    paths = [sprite_path(INV[rock]['files'][0]),
             os.path.join(R, 'before_front.png'), sorted(glob.glob(os.path.join(R, 'lod0_y*.png')))[0],
             sorted(glob.glob(os.path.join(R, 'toplit_y*.png')))[0]]
    for i, (p, label) in enumerate(zip(paths, ('native', 'before (neutral)', 'after (neutral)', 'after (top-lit)'))):
        im, st = tile(p); y = r * (T + 34)
        sheet.paste(im, (i * T, y + 34)); d.text((i * T + 4, y + 3), f'{rock} {label}', fill=(0, 0, 0))
        d.text((i * T + 4, y + 17), st, fill=(60, 60, 60))
sheet.save(out); print(out)
