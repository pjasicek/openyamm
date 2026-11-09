"""Pass 7: UV layout plot of a head_uv npz (piece colours; hidden dark; face front light) + density stats. Args: <npz> <out png>"""
import sys
import numpy as np
from PIL import Image, ImageDraw
d = np.load(sys.argv[1]); uv, tri, fp, hid, face, co = d['uv'], d['tri'], d['fpiece'], d['hidden'], d['face'], d['co']
im = Image.new('RGB', (1024, 1024), (20, 20, 20)); dr = ImageDraw.Draw(im)
col = {0: (200, 140, 120), 1: (80, 160, 90), 2: (120, 120, 220), 3: (220, 200, 80), 4: (220, 80, 80)}
for f, t in enumerate(tri):
    c = col[int(fp[f])]
    if hid[f]: c = tuple(x // 3 for x in c)
    if face[f]: c = (255, 180, 160)
    dr.polygon([(uv[i, 0] * 1024, (1 - uv[i, 1]) * 1024) for i in t], fill=c)
im.save(sys.argv[2])
a3 = np.linalg.norm(np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]]), axis=1) / 2
u = uv[tri]; a2 = np.abs((u[:, 1, 0] - u[:, 0, 0]) * (u[:, 2, 1] - u[:, 0, 1]) - (u[:, 2, 0] - u[:, 0, 0]) * (u[:, 1, 1] - u[:, 0, 1])) / 2
r = np.sqrt(a2 / np.maximum(a3, 1e-12)) * 1024 / 100      # texels per cm at 1K
for nm, m in [('face', face), ('hidden', hid), ('other', ~face & ~hid)]: print(nm, 'texels/cm p10/50/90', np.percentile(r[m], [10, 50, 90]).round(2))
# face islands: connected components over the face faces via shared uv vertices
par = np.arange(len(uv))
def f_(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for t in tri: r0 = f_(t[0]); par[f_(t[1])] = r0; par[f_(t[2])] = r0
isl = np.array([f_(t[0]) for t in tri])
print('islands', len(np.unique(isl)), 'face-front islands', len(np.unique(isl[face & (fp == 0)])), 'zero-area', int((a2 < 1e-12).sum()))
