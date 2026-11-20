#!/usr/bin/env python3
"""Front (x-z) and side (y-z) orthographic point silhouettes of a mesh npz/glb with a 5 cm grid and optional joint
markers. Usage: silhouette.py <mesh.glb> <out.png> [joints.json]"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes
d, b = read_glb(Path(sys.argv[1]))
pos = []
for n in d['nodes']:
    if 'mesh' not in n:
        continue
    for p in d['meshes'][n['mesh']]['primitives']:
        v = np.frombuffer(accessor_bytes(d, b, p['attributes']['POSITION']), np.float32).reshape(-1, 3)
        idx = np.frombuffer(accessor_bytes(d, b, p['indices']), np.uint32 if d['accessors'][p['indices']]['componentType'] == 5125 else np.uint16).reshape(-1, 3)
        pos.append((v, idx))
v, idx = pos[0]
# glTF y-up, +z forward -> blender x, -z? use x right, y up, z forward(+)
X, Y, Z = v[:, 0], v[:, 1], v[:, 2]
S = 400; pad = 40
def draw(ax_h, ax_v, flip=False):
    W = int((1.6) * S) + 2 * pad; H = int(1.95 * S) + 2 * pad
    im = Image.new('RGB', (W, H), (30, 30, 34)); dr = ImageDraw.Draw(im)
    def P(h, vv):
        return (pad + (h + 0.8) * S, pad + (1.9 - vv) * S)
    for g in np.arange(-0.8, 0.81, 0.05):
        x0, _ = P(g, 0); dr.line([(x0, pad), (x0, H - pad)], fill=(60, 60, 60) if abs(g * 20 % 2) > .5 else (90, 90, 90))
    for g in np.arange(0, 1.91, 0.05):
        _, y0 = P(0, g); dr.line([(pad, y0), (W - pad, y0)], fill=(60, 60, 60) if abs(g * 20 % 2) > .5 else (90, 90, 90))
    for t in idx:
        dr.polygon([P(ax_h[i], ax_v[i]) for i in t], fill=(200, 160, 180))
    return im, dr, P
front, df, Pf = draw(X, Y)
side, ds, Ps = draw(-Z, Y)
if len(sys.argv) > 3:
    J = json.load(open(sys.argv[3]))
    for name, (jx, jy, jz) in J.items():   # blender coords x, y(-forward), z up
        for dr, P, h in ((df, Pf, jx), (ds, Ps, jy)):
            px, py = P(h, jz); dr.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(40, 220, 90)); dr.text((px + 5, py - 6), name, fill=(255, 255, 0))
out = Image.new('RGB', (front.width + side.width, front.height)); out.paste(front, (0, 0)); out.paste(side, (front.width, 0))
out.save(sys.argv[2])
