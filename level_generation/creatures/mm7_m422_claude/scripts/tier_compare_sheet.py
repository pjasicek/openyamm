#!/usr/bin/env python3
"""Side by side per tier: native front (m422sa0) and back (m422sa4) in the tier's palette, scaled to the model's
silhouette height in the viewer shot, next to the viewer shots (review/shots/m422_<t>_tm{front,back}.png).
Writes review/tiers_vs_native.png. Args: none"""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
H = Path(__file__).resolve().parents[1]; REPO = H.parents[2]
src = json.load(open(H.parent / 'mm7_m422' / 'sources.json'))['sources']
PAL = {'a': 99, 'b': 104, 'c': 105}
BG = (86, 89, 96)


def crop_shot(p):
    im = np.asarray(Image.open(p).convert('RGB')).astype(int)
    h_, w_ = im.shape[:2]; bg = np.median(im[h_ // 2 - 50:h_ // 2 + 50, 10:60].reshape(-1, 3), 0)
    m = np.abs(im - bg).sum(-1) > 60; m[:40] = False; m[-60:] = False         # label bars and the floor grid out
    ys, xs = np.where(m); return Image.fromarray(im[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.uint8))


def native(name, p):
    ix = np.asarray(Image.open(REPO / src[name]['path']))
    pal = np.frombuffer(open(REPO / f'assets_dev/worlds/mm7/textures/pal{p:03d}.act', 'rb').read()[:768], np.uint8).reshape(256, 3)
    rgb = pal[ix]; a = ix != 0
    ys, xs = np.where(a); rgb = rgb[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy(); a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    rgb[~a] = BG; return Image.fromarray(rgb.astype(np.uint8))


rows = []
for t, p in PAL.items():
    shots = [crop_shot(H / 'review' / 'shots' / f'm422_{t}_tm{v}.png') for v in ('front', 'back')]
    h = max(s.height for s in shots)
    tiles = []
    for nat, shot in zip(('m422sa0', 'm422sa4'), shots):
        n = native(nat, p); n = n.resize((round(n.width * h / n.height), h), Image.NEAREST)
        tiles += [n, shot]
    rows.append((t, p, tiles))
W = max(sum(x.width for x in tiles) + 20 * len(tiles) for _, _, tiles in rows); Hh = sum(max(x.height for x in tiles) + 30 for _, _, tiles in rows)
S = Image.new('RGB', (W, Hh), BG); d = ImageDraw.Draw(S); y = 0
for t, p, tiles in rows:
    d.text((6, y + 6), f'tier {t.upper()} palette {p}: native front | model front | native back | model back', fill=(255, 255, 255)); y += 30; x = 10
    for im in tiles:
        S.paste(im, (x, y)); x += im.width + 20
    y += max(im.height for im in tiles)
S.save(H / 'review' / 'tiers_vs_native.png'); print('SHEET', S.size)
