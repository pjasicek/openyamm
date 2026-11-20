"""Blender: quick crown check without a build. Lays out one palm (optionally with trial settings as JSON), builds LOD0
and prints, per height band (fractions of H), the crown's largest horizontal reach from the trunk axis against the
native sprite's half-width (largest |x| from the trunk base), plus the frond fit and the raw top.
Usage: blender --background --python crown_profile.py -- <id> ['{"elev": [75, 10], ...}']"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import build_palm as bp
import palm_common as pc

S, H = bp.S, bp.H
fit = 1.0
for it in range(4 if S.get('fit') else 0):
    L = bp.layout(fit)
    top0 = max(z for _, _, z in bp.build(L, 0).co)
    fit *= (H - L['heart'].z) / max(top0 - L['heart'].z, 0.1)
L = bp.layout(fit)
co = np.array(bp.build(L, 0).co)
img = bpy.data.images.load(os.path.join(pc.SPRITES, S['sprite']))
px = np.array(img.pixels[:], np.float32).reshape(img.size[1], img.size[0], 4)[::-1]     # rows top-down
sprite = px[..., 3] > 0.5
ys, xs = np.nonzero(sprite); y0, y1 = ys.min(), ys.max(); Hs = y1 - y0 + 1; cx = (xs.min() + xs.max()) / 2
heart = L['heart']
print(f"PROFILE {bp.SID} fit {fit:.3f} raw top {co[:, 2].max() / H:.3f} H; reach from the heart axis (model | sprite)")
row = []
for f in np.arange(0.2, 1.0, 0.1):
    band = (co[:, 2] >= f * H) & (co[:, 2] < (f + 0.1) * H)
    m = np.hypot(co[band, 0] - heart.x, co[band, 1] - heart.y).max() / H if band.any() else 0.0
    yy = slice(int(y1 - (f + 0.1) * Hs), int(y1 - f * Hs))
    sx = np.nonzero(sprite[yy].any(0))[0]
    s = (max(abs(sx.min() - cx), abs(sx.max() - cx)) / Hs - 0) if len(sx) else 0.0
    row.append(f"{f:.1f}: {m:.2f}|{s:.2f}")
print('   ', '  '.join(row))
import json
print('JSON', json.dumps({'fit': fit, 'top': float(co[:, 2].max() / H), 'model': [float(r.split(':')[1].split('|')[0]) for r in row],
                          'sprite': [float(r.split('|')[1]) for r in row]}))
