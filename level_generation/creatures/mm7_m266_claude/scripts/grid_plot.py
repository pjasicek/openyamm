"""Orthographic flat-shaded projections of a dumped mesh (dump_mesh.py) with a labelled 10 cm grid and optional joint
markers, for reading joints from numbers. Views: front (x right = character's left... image x = world x, camera at -Y),
side (camera at +X looking -X: image x = -y, so the face (-Y) points image left), top (x, -y up).
Args: <npz> <out png> [joints json] [--skin-only] [--zmax Z] [--xmin X|--xmax X]"""
import sys, json
import numpy as np
from PIL import Image, ImageDraw
a = sys.argv[1:]
d = np.load(a[0]); co, tri, pv = d['co'], d['tri'], d['piece']
J = json.load(open(a[2]))['joints'] if len(a) > 2 and a[2].endswith('.json') else {}
opt = lambda k, df=None: float(a[a.index(k) + 1]) if k in a else df
if '--skin-only' in a:
    keep = pv[tri].min(1) == 0
    tri = tri[keep]
sel = np.ones(len(tri), bool)
for k, ax, sgn in (('--xmin', 0, 1), ('--xmax', 0, -1), ('--zmax', 2, -1), ('--zmin', 2, 1)):
    v = opt(k)
    if v is not None:
        c = co[tri].mean(1)[:, ax]
        sel &= (c >= v) if sgn > 0 else (c <= v)
tri = tri[sel]
S = int(__import__("os").environ.get("GS", "300"))  # px per metre
views = {'front': (0, 2, 1, 1), 'side': (1, 2, 0, -1), 'top': (0, 1, 2, 1)}
ims = []
for name, (ix, iy, idep, sx) in views.items():
    p = co.copy()
    X = p[:, ix] * (sx if name != 'side' else -1); Y = p[:, iy]
    if name == 'top':
        Y = -p[:, 1]
    lo = np.array([X.min(), Y.min()]) - 0.1; hi = np.array([X.max(), Y.max()]) + 0.1
    W, H = int((hi[0] - lo[0]) * S), int((hi[1] - lo[1]) * S)
    im = Image.new('RGB', (W, H), (235, 235, 235)); dr = ImageDraw.Draw(im)
    px = lambda x, y: ((x - lo[0]) * S, H - (y - lo[1]) * S)
    for g in np.arange(np.floor(lo[0] * 10) / 10, hi[0], 0.1):
        dr.line([px(g, lo[1]), px(g, hi[1])], fill=(200, 200, 255) if abs(g) > 1e-6 else (120, 120, 255))
        dr.text(px(g + 0.005, hi[1] - 0.03), f'{g:.1f}', fill=(80, 80, 200))
    for g in np.arange(np.floor(lo[1] * 10) / 10, hi[1], 0.1):
        dr.line([px(lo[0], g), px(hi[0], g)], fill=(200, 200, 255))
        dr.text(px(lo[0] + 0.005, g + 0.02), f'{g:.1f}', fill=(80, 80, 200))
    # painter's algorithm: far first. front camera at -Y (depth = +y far), side camera at +X (depth = -x far), top from +Z
    dep = co[tri].mean(1)[:, idep]
    order = np.argsort(-dep if name == 'front' else dep if name == 'side' else dep)
    n = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    L = np.array({'front': (0.3, -0.8, 0.5), 'side': (0.8, -0.3, 0.5), 'top': (0.3, -0.3, 0.9)}[name])
    sh = np.abs(n @ (L / np.linalg.norm(L)))
    for t in order:
        v = tri[t]
        c = int(80 + 150 * sh[t]); col = (c, c, c) if pv[v[0]] == 0 else (c // 2, c, c // 2)
        dr.polygon([px(X[i], Y[i]) for i in v], fill=col)
    for k, j in J.items():
        jx = j[ix] * (sx if name != 'side' else -1); jy = j[iy] if name != 'top' else -j[1]
        x, y = px(jx, jy)
        dr.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 0, 0)); dr.text((x + 5, y - 5), k, fill=(200, 0, 0))
    dr.text((4, 4), name, fill=(0, 0, 0))
    ims.append(im)
Wt = sum(i.width for i in ims); Ht = max(i.height for i in ims)
out = Image.new('RGB', (Wt, Ht), (255, 255, 255)); x = 0
for i in ims:
    out.paste(i, (x, 0)); x += i.width
out.save(a[1])
print('GRID', out.size)
