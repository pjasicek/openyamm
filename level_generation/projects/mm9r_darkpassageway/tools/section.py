#!/usr/bin/env python3
"""Side view of the static polygons in a box: tools/section.py out.png x0 x1 z0 z1 [--axis x|z]
Draws polygons (projected on z-y when --axis z, i.e. looking along x; else x-y), coloured by texture, with objects."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mm9r_common"))
from dungeon.source import Project, Source
p = Project.load(Path(__file__).resolve().parents[1], install=False)
s = Source(p)
out, x0, x1, z0, z1 = sys.argv[1], *map(float, sys.argv[2:6])
axis = sys.argv[sys.argv.index("--axis") + 1] if "--axis" in sys.argv else "z"
h = 0 if axis == "x" else 2
polys = []
pal = [(230,25,75),(60,180,75),(255,225,25),(0,130,200),(245,130,48),(145,30,180),(70,240,240),(240,50,230),(210,245,60),(250,190,212),(0,128,128),(220,190,255),(170,110,40),(255,250,200),(128,0,0),(170,255,195),(128,128,0),(255,215,180),(0,0,128),(200,200,200)]
cmap = {}
for name in s.models:
    if name in ("VisBSP",) or name.startswith(("AITrk",)):
        continue
    try:
        found = s.polygons(name)
    except KeyError:
        continue
    for poly in found:
        pts = poly.points; c = pts.mean(0)
        if not (x0 <= c[0] <= x1 and z0 <= c[2] <= z1):
            continue
        tex = poly.texture.split("\\")[-1].lower()
        cmap.setdefault(tex, pal[len(cmap) % 20])
        polys.append((pts[:, [h, 1]], cmap[tex] if poly.role == "static" else (90, 90, 90), name))
allp = np.concatenate([q[0] for q in polys])
lo, hi = allp.min(0) - 50, allp.max(0) + 50
S = min(2400 / (hi[0] - lo[0]), 1400 / (hi[1] - lo[1]))
W, H = int((hi[0] - lo[0]) * S) + 300, int((hi[1] - lo[1]) * S)
im = Image.new("RGB", (W, H), (20, 20, 28)); d = ImageDraw.Draw(im)
f = lambda u, v: ((u - lo[0]) * S, H - (v - lo[1]) * S)
for gy in range(int(lo[1] // 128 * 128), int(hi[1]), 128):
    d.line([f(lo[0], gy), f(hi[0], gy)], fill=(45, 45, 55)); d.text(f(lo[0], gy), str(gy), fill=(120, 120, 120))
for gx in range(int(lo[0] // 512 * 512), int(hi[0]), 512):
    d.line([f(gx, lo[1]), f(gx, hi[1])], fill=(45, 45, 55)); d.text(f(gx, hi[1] - 30), str(gx), fill=(120, 120, 120))
for pts, col, name in polys:
    d.polygon([f(u, v) for u, v in pts], outline=col)
objs = json.loads((p.directory / "work/dat_objects.json").read_text())
for o in objs:
    pos = o["properties"].get("Pos")
    if not pos or o["class"] in ("AmbientSound", "PerceptionLight", "Light", "ObjectLight", "Marker"):
        continue
    if x0 <= pos[0] <= x1 and z0 <= pos[2] <= z1:
        u, v = f(pos[h], pos[1]); d.ellipse([u - 2, v - 2, u + 2, v + 2], fill=(255, 255, 255)); d.text((u + 3, v), o["name"], fill=(255, 255, 255))
for i, (t2, c) in enumerate(cmap.items()):
    d.text((W - 290, 10 + 12 * i), t2, fill=c)
im.save(out)
