#!/usr/bin/env python3
"""Plan picture of sectors' floor faces coloured by height, with the rebuild's room outlines over it.
Usage: draw.py out.png x0 y0 x1 y1 [zmin zmax]"""
import sys, json
from PIL import Image, ImageDraw
from lib import *
out, x0, y0, x1, y1 = sys.argv[1], *[float(v) for v in sys.argv[2:6]]
zmin = float(sys.argv[6]) if len(sys.argv) > 6 else -1e9
zmax = float(sys.argv[7]) if len(sys.argv) > 7 else 1e9
W = 1400; sc = W / (x1 - x0); H = int((y1 - y0) * sc)
im = Image.new('RGB', (W, H), (20, 20, 24)); dr = ImageDraw.Draw(im)
def px(p): return ((p[0] - x0) * sc, H - (p[1] - y0) * sc)
faces = []
for si, s in enumerate(S):
    for fi in s['floor_faces']:
        p = fpts(F[fi]); z = sum(q[2] for q in p) / len(p)
        if zmin <= z <= zmax: faces.append((z, p, max(q[2] for q in p) - min(q[2] for q in p) > 2))
faces.sort(key=lambda t: t[0])
zs = [f[0] for f in faces] or [0]
lo, hi = min(zs), max(zs) + 1
for z, p, sl in faces:
    t = (z - lo) / (hi - lo)
    col = (int(40 + 200 * t), int(200 - 120 * abs(t - 0.5) * 2), int(240 - 200 * t)) if not sl else (int(90 + 150 * t), int(90 + 60 * t), 60)
    dr.polygon([px(q) for q in p], fill=col, outline=(0, 0, 0))
try:
    g = json.load(open(D + 'gen_rooms.json'))
    for r in g['rooms']:
        lo_ = min(r['floor'], r['floor_high'])
        if lo_ > zmax or r['floor_high'] < zmin: continue
        pts = [px(q) for q in r['pts']]
        dr.line(pts + [pts[0]], fill=(255, 255, 255), width=2)
except Exception as e:
    print(e)
# height labels
seen = set()
for z, p, sl in faces:
    cx = sum(q[0] for q in p) / len(p); cy = sum(q[1] for q in p) / len(p)
    key = (int(cx * sc / 60), int(cy * sc / 30))
    if key in seen or sl: continue
    seen.add(key)
    dr.text(px((cx, cy)), '%d' % z, fill=(0, 0, 0))
im.save(out)
