#!/usr/bin/env python3
"""Top view of up-facing static polygons coloured by height (low blue -> high red), labelled every few with their
height; objects marked. tools/heights.py out.png x0 x1 z0 z1 [ymin ymax]"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mm9r_common"))
from dungeon.source import Project, Source
p = Project.load(Path(__file__).resolve().parents[1], install=False)
s = Source(p)
out, x0, x1, z0, z1 = sys.argv[1], *map(float, sys.argv[2:6])
ymin, ymax = (float(sys.argv[6]), float(sys.argv[7])) if len(sys.argv) > 7 else (-1e9, 1e9)
polys = []
for name in s.models:
    if name == "VisBSP" or name.startswith("AITrk"):
        continue
    try:
        found = s.polygons(name)
    except KeyError:
        continue
    for poly in found:
        c = poly.points.mean(0)
        if poly.normal[1] > 0.3 and x0 <= c[0] <= x1 and z0 <= c[2] <= z1 and ymin <= c[1] <= ymax:
            polys.append((c[1], poly.points, poly.role, name))
polys.sort(key=lambda q: q[0])
ys = np.array([q[0] for q in polys]); lo, hi = ys.min(), ys.max()
S = min(1800 / (x1 - x0), 1800 / (z1 - z0))
W, H = int((x1 - x0) * S), int((z1 - z0) * S)
im = Image.new("RGB", (W, H), (15, 15, 20)); d = ImageDraw.Draw(im)
f = lambda x, z: ((x - x0) * S, (z1 - z) * S)
for y, pts, role, name in polys:
    t = (y - lo) / max(1, hi - lo)
    col = (int(255 * t), int(80 + 100 * (1 - abs(t - 0.5) * 2)), int(255 * (1 - t)))
    if role != "static":
        col = (90, 90, 90)
    d.polygon([f(q[0], q[2]) for q in pts], fill=col, outline=(0, 0, 0))
for y, pts, role, name in polys:
    c = pts.mean(0); area = (pts[:, 0].max() - pts[:, 0].min()) * (pts[:, 2].max() - pts[:, 2].min())
    if area > 20000:
        d.text(f(c[0], c[2]), str(int(y)), fill=(255, 255, 255))
for gx in range(int(x0 // 256 * 256), int(x1), 256):
    d.line([f(gx, z0), f(gx, z1)], fill=(60, 60, 60)); d.text(f(gx, z1), str(gx), fill=(200, 200, 200))
for gz in range(int(z0 // 256 * 256), int(z1), 256):
    d.line([f(x0, gz), f(x1, gz)], fill=(60, 60, 60)); d.text(f(x0, gz), str(gz), fill=(200, 200, 200))
objs = json.loads((p.directory / "work/dat_objects.json").read_text())
for o in objs:
    pos = o["properties"].get("Pos")
    if not pos or o["class"] in ("AmbientSound", "PerceptionLight", "Light", "ObjectLight", "Marker", "Prop"):
        continue
    if x0 <= pos[0] <= x1 and z0 <= pos[2] <= z1:
        u, v = f(pos[0], pos[2]); d.ellipse([u - 3, v - 3, u + 3, v + 3], fill=(255, 255, 255)); d.text((u + 4, v), f"{o['name']} {int(pos[1])}", fill=(255, 255, 0))
im.save(out); print("heights", lo, hi)
