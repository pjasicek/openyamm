#!/usr/bin/env python3
"""Native evidence sheets for the HD master brief (originals only, nearest-neighbour x3 on flat grey):
source/native_standing_views.png (sa0..sa4), source/native_actions.png (fidget, hit, death front frames),
source/native_tiers.png (stand front in every tier palette). Args: <native project> <prefix> <palettes comma list>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
nat, pre, pals = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(',')]
N = HERE.parent / nat / 'native'
PALDIR = HERE.parents[2] / 'assets_dev' / 'worlds' / 'mm7' / 'textures'
OUT = HERE / 'source'; OUT.mkdir(exist_ok=True)


def crop(ims):
    bb = [i.getbbox() for i in ims]
    x0 = min(b[0] for b in bb) - 6; y0 = min(b[1] for b in bb) - 6; x1 = max(b[2] for b in bb) + 6; y1 = max(b[3] for b in bb) + 6
    return [i.crop((x0, y0, x1, y1)) for i in ims]


def sheet(names, path, k=3, ims=None):
    ims = ims or [Image.open(N / f'{n}.png').convert('RGBA') for n in names]
    ims = crop(ims)
    w, h = ims[0].size
    s = Image.new('RGB', (w * k * len(ims), h * k), (128, 128, 128))
    for i, im in enumerate(ims):
        im = im.resize((w * k, h * k), Image.NEAREST)
        s.paste(im, (i * w * k, 0), im)
    s.save(path); print('SHEET', path, s.size)


sheet([f'{pre}sa{i}' for i in range(5)], OUT / 'native_standing_views.png')
acts = [f'{pre}f{c}0' for c in 'abcd'] + [f'{pre}n{c}0' for c in 'abcdefg'] + [f'{pre}d{c}0' for c in 'abcd']
sheet([a for a in acts if (N / f'{a}.png').exists()], OUT / 'native_actions.png', k=2)
pal = lambda i: np.frombuffer(open(PALDIR / f'pal{i:03d}.act', 'rb').read()[:768], np.uint8).reshape(256, 3)
base = pal(pals[0]); lut = {tuple(c): i for i, c in enumerate(base.astype(int))}
a = np.asarray(Image.open(N / f'{pre}sa0.png').convert('RGBA'))
m = a[..., 3] > 0
idx = np.full(m.shape, -1); idx[m] = [lut.get(tuple(c), -1) for c in a[m][:, :3].astype(int)]
print('UNMAPPED pixels', int((idx[m] < 0).sum()), 'of', int(m.sum()))
tiers = []
for p in pals:
    out = a.copy(); P = pal(p); ok = m & (idx >= 0); out[ok, :3] = P[idx[ok]]; tiers.append(Image.fromarray(out))
sheet(None, OUT / 'native_tiers.png', k=2, ims=tiers)
