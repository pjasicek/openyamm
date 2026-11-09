#!/usr/bin/env python3
"""Soften red lid rims (user on PeasantM1, 2026-11-01: no heavy red rims; mm9_bjarni 2026-11-02: the head paint's lower lids
read pink-red from party distance). Head-set texels whose bind-pose surface point lies within RADIUS of an eye centre (the
centroid of that side's iris texels) and that are red-dominant (r/g > RATIO, saturation > 0.3) move AMOUNT of the way toward
the median skin colour of a ring 2.2-3.2 cm around the eye, keeping their own luminance detail. Irises, sclera, lashes and
brows are not red-dominant and stay. Runs on textures/bj_tp_head_basecolor.png in place, last in the head chain.
Usage (project folder): eye_rim_fix.py <runtime glb> [amount 0.6] [radius 0.02] [ratio 1.45]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402

GLBP = sys.argv[1]
AMOUNT = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6
RADIUS = float(sys.argv[3]) if len(sys.argv) > 3 else 0.02
RATIO = float(sys.argv[4]) if len(sys.argv) > 4 else 1.45
T = Path('textures/bj_tp_head_basecolor.png')
img = np.asarray(Image.open(T).convert('RGB')).astype(np.float64) / 255
N = img.shape[0]
glb = Glb(Path(GLBP)); model = Model(glb); doc = glb.json
node0 = model.primitives[0]['node']; mesh = doc['meshes'][doc['nodes'][node0]['mesh']]
k = next(i for i, p in enumerate(mesh['primitives']) if 'Head' in doc['materials'][p.get('material', 0)]['name'])
X = model.skinned_positions(model.world({}))[k][0]
uv = glb.accessor(mesh['primitives'][k]['attributes']['TEXCOORD_0']).astype(np.float64)
I = model.primitives[k]['triangles']
ys, xs, ps = [], [], []
for tri in I:
    q = uv[tri] * N
    x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
    gx, gy = np.meshgrid(np.arange(max(x0, 0), min(x1, N)), np.arange(max(y0, 0), min(y1, N)))
    if gx.size == 0:
        continue
    pts = np.stack([gx.ravel() + 0.5, gy.ravel() + 0.5], 1)
    a, b, c = q
    m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
    if abs(np.linalg.det(m)) < 1e-12:
        continue
    l = np.linalg.solve(m, (pts - a).T).T
    ok = (l >= -0.01).all(1) & (l.sum(1) <= 1.01)
    if not ok.any():
        continue
    l = l[ok]; bc = np.stack([1 - l.sum(1), l[:, 0], l[:, 1]], 1)
    ys.append(pts[ok, 1].astype(int)); xs.append(pts[ok, 0].astype(int)); ps.append(bc @ X[tri])
ty, tx, tp = np.concatenate(ys), np.concatenate(xs), np.concatenate(ps)
col = img[ty, tx]
r, g, b = col[:, 0], col[:, 1], col[:, 2]
iris = (b > r * 1.15) & (b > 0.3)
head_top = tp[:, 1] > tp[:, 1].max() - 0.35          # the head (hands hang lower)
eyes = []
for sgn in (-1, 1):
    m = iris & head_top & (np.sign(tp[:, 0] - np.median(tp[iris & head_top, 0])) == sgn)
    eyes.append(np.median(tp[m], 0))
mx, mn = col.max(1), col.min(1)
sat = (mx - mn) / np.maximum(mx, 1e-6)
lum = col @ np.array([0.299, 0.587, 0.114])
out = img.copy(); total = 0
mask = np.zeros((N, N), bool)
for e in eyes:
    d = np.linalg.norm(tp - e, axis=1)
    ring = (d > 0.022) & (d < 0.032) & (sat > 0.2) & (sat < 0.6) & (lum > 0.35)
    skin = np.median(col[ring], 0)
    red = (d < RADIUS) & (r > g * RATIO) & (sat > 0.3) & ~iris
    w = AMOUNT * np.clip((RADIUS - d[red]) / (0.3 * RADIUS), 0, 1)[:, None]
    tgt = skin[None, :] * (lum[red] / max(skin @ np.array([0.299, 0.587, 0.114]), 1e-6))[:, None]
    out[ty[red], tx[red]] = col[red] * (1 - w) + tgt * w
    mask[ty[red], tx[red]] = True; total += int(red.sum())
    print('EYE', e.round(3).tolist(), 'ring skin', (skin * 255).round(0).tolist(), 'red texels', int(red.sum()))
grow = ndi.binary_dilation(mask, iterations=1)
blur = ndi.gaussian_filter(out, (0.6, 0.6, 0))
out[grow] = blur[grow]
Image.fromarray(np.uint8(np.clip(out, 0, 1) * 255 + 0.5)).save(T)
print('EYE_RIM_FIX texels', total)
