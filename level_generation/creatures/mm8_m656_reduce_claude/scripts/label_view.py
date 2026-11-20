"""Painter's-algorithm projection of the rest mesh with per-face colours (quick label checks).
Usage: label_view.py <out.png> <view: front|side|back> <zmin> <zmax> <colour source: tex|mask:<npy>>"""
import sys
import numpy as np
from PIL import Image, ImageDraw
d = np.load('work/mesh_in.npz'); fi = np.load('work/face_info.npz')
f, v = d['faces'], d['verts']
out, view, zmin, zmax, src = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
ax = {'front': (0, 2, 1, 1), 'back': (0, 2, 1, -1), 'side': (1, 2, 0, -1)}[view]
c = v[f].mean(1); sel = np.where((c[:, 2] >= zmin) & (c[:, 2] <= zmax))[0]
if src == 'tex':
    cols = (fi['col'] * 255).astype(int)
else:
    m = np.load(src.split(':', 1)[1])
    cols = np.where(m[:, None] if m.dtype == bool else (m[:, None] > 0), [[230, 40, 40]], [[150, 150, 150]])
    if m.dtype != bool:
        pal = np.array([[150, 150, 150], [230, 40, 40], [40, 160, 230], [60, 200, 60], [230, 200, 40], [200, 60, 220], [240, 140, 40], [40, 220, 200], [120, 80, 40]])
        cols = pal[np.clip(m, 0, len(pal) - 1)]
P = v[f][sel]; xs = P[:, :, ax[0]] * (ax[3] if view != 'side' else 1); zs = P[:, :, ax[1]]
dep = P[:, :, ax[2]].mean(1) * (1 if view == 'front' else -1) * (1 if view != 'side' else ax[3])
x0, x1, z0, z1 = xs.min(), xs.max(), zs.min(), zs.max(); S = 900 / max(x1 - x0, z1 - z0)
im = Image.new('RGB', (int((x1 - x0) * S) + 20, int((z1 - z0) * S) + 20), (30, 30, 34)); dr = ImageDraw.Draw(im)
nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
for i in np.argsort(-dep):  # far first (front view looks along +y: larger y is farther)
    k = sel[i]; shade = 0.55 + 0.45 * abs(nrm[i][ax[2]])
    dr.polygon([(10 + (xs[i, j] - x0) * S, 10 + (z1 - zs[i, j]) * S) for j in range(3)], fill=tuple(int(q * shade) for q in cols[k]))
im.save(out)
