#!/usr/bin/env python3
"""Binding scale from the native sprite: the front silhouette above the water (alpha area, width, height) of the
octopod in Darkside 041.mon frames 0, 4, 5 (the lake's teal pixels and everything below the water row left out) at the
Xeen bindings' 1.34 units/px, against the model's front silhouette above z 0 in Standing (mean over 6 times; the foam
ring left out). Usage: scale_measure.py <glb>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared' / 'floor'))
import glb_pose as G

UPX = 1.34
nats = []
for f in ('mon_0000', 'mon_0004', 'mon_0005'):
    a = np.asarray(Image.open(ROOT / 'native' / f'{f}.png').convert('RGBA')).astype(float) / 255
    rgb = a[..., :3]; al = a[..., 3] > 0
    teal = al & (rgb[..., 1] > rgb[..., 0] + 0.05) & (rgb[..., 2] > rgb[..., 0] + 0.05)
    ys, _ = np.nonzero(teal); water = int(np.percentile(ys, 20))          # the lake's top rows
    body = al & ~teal; body[water:] = False
    ys, xs = np.nonzero(body)
    nats.append(dict(area=float(body.sum()) * UPX ** 2, width=(xs.max() - xs.min() + 1) * UPX,
                     height=(water - ys.min()) * UPX))
nat = {k: float(np.mean([n[k] for n in nats])) for k in nats[0]}
m = G.Model(G.Glb(sys.argv[1]))
mods = []
for t in np.linspace(0, 2.5, 6):
    posed = m.skinned_positions(m.world(m.sample('Standing', float(t))))
    RES = 500.0
    img = Image.new('L', (2000, 1000), 0); d = ImageDraw.Draw(img)
    for pts, tris in posed:
        if len(pts) < 1000:
            continue
        for tr in tris:
            p = pts[tr]
            d.polygon([(1000 + q[0] * RES, 900 - max(q[1], 0.0) * RES) for q in p], fill=255)
    mm = np.asarray(img)[:900] > 0
    ys2, xs2 = np.nonzero(mm)
    mods.append(dict(area=float(mm.sum()) / RES ** 2, width=(xs2.max() - xs2.min() + 1) / RES, height=(900 - ys2.min()) / RES))
mod = {k: float(np.mean([n[k] for n in mods])) for k in mods[0]}
print('NATIVE units', {k: round(v, 1) for k, v in nat.items()})
print('MODEL m', {k: round(v, 3) for k, v in mod.items()})
print('SCALE by area', round((nat['area'] / mod['area']) ** 0.5, 1), 'by height', round(nat['height'] / mod['height'], 1),
      'by width', round(nat['width'] / mod['width'], 1))
