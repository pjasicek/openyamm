#!/usr/bin/env python3
"""Two small face-paint touches after project_face.py (mm9_tryggva face pass, 2026-11-02; brief: "chin smudges"):
- chin: a pale rim along the jaw's lower edge (a tone step from the jaw, 150/99/73, to the neck, 136/84/60): head texels in
  the band y CHIN0..CHIN1 (glTF metres, rest pose), |x| < 0.06, front half, take 60 % of the mean of their 1 cm 3D
  neighbourhood (the step becomes a soft gradient);
- tear streak: a dark streak under his left eye (image right in the front render) left by the eye repaint: texels
  within 5 mm of TEAR darker than 0.93 x their neighbourhood median take that median.
Colours only. Positions from the export GLB (rest pose, the same frame as render_face.py/project_face.py). Reads and
writes textures/try_tp_head_basecolor.png (backup *_pretouch.png on the first run, read from there).
Usage (project folder): face_touch.py <export glb>"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from pygltflib import GLTF2

CHIN0, CHIN1 = 1.546, 1.568
TEAR = np.array([0.0305, 1.6545])
R = 0.006
g = GLTF2().load(sys.argv[1]); blob = g.binary_blob()


def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]
    return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).astype(np.float64)


hp = next(p for m in g.meshes[:1] for p in m.primitives if g.materials[p.material].name.endswith('Head'))
P = acc(hp.attributes.POSITION); UV = acc(hp.attributes.TEXCOORD_0); T = acc(hp.indices).astype(int).reshape(-1, 3)
f = Path('textures/try_tp_head_basecolor.png'); bk = f.with_name(f.stem + '_pretouch.png')
if not bk.exists():
    shutil.copyfile(f, bk)
img = np.asarray(Image.open(bk).convert('RGB'), float); N = img.shape[0]
pos = np.full((N, N, 3), np.nan)
for t in T:
    uv = UV[t] * N
    if P[t][:, 1].max() < 1.50 or P[t][:, 1].min() > 1.70:
        continue
    x0, y0 = np.maximum(np.floor(uv.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(uv.max(0)).astype(int), N - 1)
    if x1 < x0 or y1 < y0:
        continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a_, b_, c_ = uv
    den = (b_[1] - c_[1]) * (a_[0] - c_[0]) + (c_[0] - b_[0]) * (a_[1] - c_[1])
    if abs(den) < 1e-12:
        continue
    l0 = ((b_[1] - c_[1]) * (gx - c_[0]) + (c_[0] - b_[0]) * (gy - c_[1])) / den
    l1 = ((c_[1] - a_[1]) * (gx - c_[0]) + (a_[0] - c_[0]) * (gy - c_[1])) / den
    L = np.stack([l0, l1, 1 - l0 - l1], -1); ins = (L >= -1e-3).all(-1)
    yy, xx = (gy[ins] - 0.5).astype(int), (gx[ins] - 0.5).astype(int)
    pos[yy, xx] = L[ins] @ P[t]
cov = ~np.isnan(pos[..., 0])
ty, tx = np.nonzero(cov)
X = pos[ty, tx]
tree = cKDTree(X)
lum = img[ty, tx] @ np.array([0.299, 0.587, 0.114])
out = img.copy(); rep = {}
front = X[:, 2] > 0.0
for name, sel, cond in (
        ('chin', (X[:, 1] > CHIN0) & (X[:, 1] < CHIN1) & (np.abs(X[:, 0]) < 0.06) & front, lambda l, m: l > m * 1.04),
        ('tear', (np.linalg.norm(X[:, :2] - TEAR, axis=1) < 0.005) & front, lambda l, m: l < m * 0.93)):
    idx = np.nonzero(sel)[0]; n = 0
    for i in idx:
        nb = tree.query_ball_point(X[i], R if name == 'chin' else 0.008)
        m = np.median(lum[nb])
        if name == 'chin':      # soften the tone step at the jaw's lower edge: 60 % of the 1 cm neighbourhood mean
            nb = tree.query_ball_point(X[i], 0.010)
            out[ty[i], tx[i]] = 0.6 * img[ty[nb], tx[nb]].mean(0) + 0.4 * img[ty[i], tx[i]]; n += 1
        elif cond(lum[i], m):
            col = np.median(img[ty[nb], tx[nb]], axis=0)
            out[ty[i], tx[i]] = col; n += 1
    rep[name] = (len(idx), n)
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f)
print('FACE_TOUCH', rep)
