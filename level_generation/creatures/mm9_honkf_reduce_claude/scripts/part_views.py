#!/usr/bin/env python3
"""Debug views of the installed LOD0 faces (orthographic, painter's order by depth): each face filled with its tier colour
(base colour at the face centroid UV) or with a class colour. Usage: part_views.py <out.png> [sets npz] [region: all|head]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
out = sys.argv[1]; sets = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != '-' else None
region = sys.argv[3] if len(sys.argv) > 3 else 'all'
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_honkf.glb', 'HonkF')
PR = ['HonkF_A', 'HonkFHead']
tex = {p: [np.asarray(Image.open(HERE / 'work' / f'tex_{p}_{k}.png').convert('RGB')) for k in (0, 1)] for p in PR}
FV, COL = [], []
for p in PR:
    P, T, UV = D[p]['P'], D[p]['T'], D[p]['UV']
    im = tex[p][0] if p == 'HonkFHead' else tex[p][0]
    u = UV[T].mean(1); H, W = im.shape[:2]
    c = im[np.clip((u[:, 1] % 1) * H, 0, H - 1).astype(int), np.clip((u[:, 0] % 1) * W, 0, W - 1).astype(int)]
    FV.append(P[T]); COL.append(c)
FV = np.concatenate(FV); COL = np.concatenate(COL).astype(float)
if sets:
    s = np.load(sets); pal = np.array([[200, 200, 200], [230, 80, 60], [60, 160, 230], [90, 200, 90], [230, 200, 60],
                                       [180, 90, 220], [240, 140, 40], [40, 220, 200], [255, 120, 180], [120, 120, 255]], float)
    COL = pal[s['group'] % len(pal)].copy(); COL[s['keep']] = [140, 20, 20]; COL[s['lining']] = [30, 30, 30]
sel = np.ones(len(FV), bool)
if region == 'head':
    sel = FV[:, :, 1].min(1) > 1.25
FV, COL = FV[sel], COL[sel]
views = {'front': (0, 1, 2, 1), 'side': (2, 1, 0, -1), 'back': (0, 1, 2, -1), 'oside': (2, 1, 0, 1)}
lo = FV.reshape(-1, 3).min(0); hi = FV.reshape(-1, 3).max(0)
S = 900 / max(hi[1] - lo[1], 1e-6) if region == 'head' else 900 / (hi[1] - lo[1])
imgs = []
for name, (a, b, dz, sg) in views.items():
    n = np.cross(FV[:, 1] - FV[:, 0], FV[:, 2] - FV[:, 0])
    vis = n[:, dz] * sg > 0
    order = np.argsort(FV[:, :, dz].mean(1) * sg)
    w = int((hi[a] - lo[a]) * S) + 20 if a != 2 else int((hi[2] - lo[2]) * S) + 20
    im = Image.new('RGB', (max(w, 200), 920), (60, 60, 70)); d = ImageDraw.Draw(im)
    for f in order:
        if not vis[f]:
            continue
        xs = (FV[f, :, a] - lo[a]) * S * (sg if a == 0 else -sg if a == 2 else 1)
        xs = xs if (a == 0 and sg > 0) or (a == 2 and sg < 0) else (hi[a] - lo[a]) * S - (FV[f, :, a] - lo[a]) * S
        ys = 910 - (FV[f, :, b] - lo[b]) * S
        lit = 0.55 + 0.45 * abs(n[f, dz]) / max(np.linalg.norm(n[f]), 1e-12)
        d.polygon(list(zip(xs + 10, ys)), fill=tuple(int(x * lit) for x in COL[f]))
    imgs.append(im)
W = sum(i.width for i in imgs); sh = Image.new('RGB', (W, 920)); x = 0
for i in imgs:
    sh.paste(i, (x, 0)); x += i.width
sh.save(out); print('WROTE', out, sh.size)
