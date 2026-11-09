#!/usr/bin/env python3
"""Flat patches in the head paint (mm9_bjarni, 2026-11-02): Meshy's 4K head retexture left some small head triangles
unpainted (one gutter colour per triangle): sharp-edged brown squares beside the nose, under the eye and on the moustache.
Every head triangle (head square of the head set, hands excluded) is rasterised; a triangle whose texels are flat
(per-channel std below STD) and whose mean differs from the texels of the triangles around it in 3D takes, texel by texel,
the colour of the nearest painted texel on the surface (3D, bind pose; nearest unflagged texel within 3 cm), then a small
blur inside the patch. Reads the runtime GLB (LOD0 head primitive) and textures/mk_tp_head_basecolor.png (in place, run after
fringe_fix.py and hand_clean.py; the first input is kept as work/mk_tp_head_basecolor_prepatch.png). Writes review/head_patch_mask.png.
Usage (project folder): head_patch_fix.py <runtime glb> [std ratio 0.5] [colour diff 0.06] [--dry]"""
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
DRY = '--dry' in sys.argv
GLBP = args[0]
STD_RATIO = float(args[1]) if len(args) > 1 else 0.5
DIFF = float(args[2]) if len(args) > 2 else 0.06
SRC = Path('work/mk_tp_head_basecolor_prepatch.png')
OUT = Path('textures/mk_tp_head_basecolor.png')
if not SRC.exists() and not DRY:
    shutil.copyfile(OUT, SRC)
img = np.asarray(Image.open(OUT).convert('RGB')).astype(np.float64) / 255   # in place, after fringe_fix/hand_clean
N = img.shape[0]
glb = Glb(Path(GLBP)); model = Model(glb)
doc = glb.json
W = model.world({})
node0 = model.primitives[0]['node']
mesh = doc['meshes'][doc['nodes'][node0]['mesh']]
k = next(i for i, p in enumerate(mesh['primitives']) if 'Head' in doc['materials'][p.get('material', 0)]['name'])
X = model.skinned_positions(W)[k][0]
uv = glb.accessor(mesh['primitives'][k]['attributes']['TEXCOORD_0']).astype(np.float64)
I = model.primitives[k]['triangles']


def raster(tri):
    q = uv[tri] * N
    x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)), np.arange(max(y0, 0), min(y1, N)))
    if xs.size == 0:
        return None
    pts = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    a, b, c = q
    m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
    if abs(np.linalg.det(m)) < 1e-12:
        return None
    l = np.linalg.solve(m, (pts - a).T).T
    ok = (l >= -0.01).all(1) & (l.sum(1) <= 1.01)
    if not ok.any():
        return None
    l = l[ok]
    bc = np.stack([1 - l.sum(1), l[:, 0], l[:, 1]], 1)
    return pts[ok, 1].astype(int), pts[ok, 0].astype(int), bc @ X[tri]


tex_y, tex_x, tex_p, tex_f = [], [], [], []
stats = {}
for fi, tri in enumerate(I):
    r = raster(tri)
    if r is None:
        continue
    yy, xx, pp = r
    tex_y.append(yy); tex_x.append(xx); tex_p.append(pp); tex_f.append(np.full(len(yy), fi))
    c = img[yy, xx]
    if (xx > 0.8 * N).all() and (yy < 0.4 * N).all():      # hand squares: hand_clean.py repaints them
        continue
    if ((c[:, 2] > c[:, 0] * 1.1) & (c[:, 2] > 0.25)).mean() > 0.05:   # iris texels: never touch the eyes
        continue
    stats[fi] = (c.mean(0), c.std(0).mean(), len(yy))
ty = np.concatenate(tex_y); tx = np.concatenate(tex_x); tp = np.concatenate(tex_p); tf = np.concatenate(tex_f)
# Meshy paints from the reference views; a head triangle that none of them sees (facing away or hidden under the nose,
# the brow or the moustache) gets its padding instead. Visibility: ray from the triangle centre toward each view
# (front, both three-quarters, both profiles, back; horizontal), blocked by any other head triangle; facing > 0.15.
cen = X[I].mean(1)
nrm = np.cross(X[I[:, 1]] - X[I[:, 0]], X[I[:, 2]] - X[I[:, 0]])
area = np.linalg.norm(nrm, axis=1); nrm /= np.maximum(area[:, None], 1e-12)
up = np.array([0.0, 1.0, 0.0])                     # glTF y up
hc = cen.mean(0)
hz = cen - hc; hz -= np.outer(hz @ up, up)
far = np.argmax(np.linalg.norm(hz, axis=1) * (np.abs((cen - hc) @ up) < 0.03))   # nose tip: farthest at mid height
fwd = hz[far] / np.linalg.norm(hz[far])
side = np.cross(up, fwd)
views = [np.cos(np.radians(a)) * fwd + np.sin(np.radians(a)) * side for a in (0, 35, -35, 90, -90, 180)]
A, B, C = X[I[:, 0]], X[I[:, 1]], X[I[:, 2]]
E1, E2 = B - A, C - A


def occluded(o, d):
    """Moller-Trumbore of one ray against every head triangle; True if something is hit beyond 1 mm."""
    pv = np.cross(d, E2); det = (E1 * pv).sum(1)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    tv = o - A; u = (tv * pv).sum(1) * inv
    qv = np.cross(tv, E1); v = (qv @ d) * inv; t = (E2 * qv).sum(1) * inv
    return bool((ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-3)).any())


seen = np.zeros(len(I), bool)
for fi in stats:
    for d in views:
        if nrm[fi] @ d > 0.15 and not occluded(cen[fi] + nrm[fi] * 5e-4, d):
            seen[fi] = True
            break
bad = {fi for fi in stats if not seen[fi]}
flat = bad
isbad = np.array([f in bad for f in tf])
src = ~isbad
tree = cKDTree(tp[src])
d, j = tree.query(tp[isbad], k=6)
w = 1.0 / np.maximum(d, 1e-4)
col = (img[ty[src][j], tx[src][j]] * w[..., None]).sum(1) / w.sum(1)[:, None]
out = img.copy()
out[ty[isbad], tx[isbad]] = col
mask = np.zeros((N, N), bool); mask[ty[isbad], tx[isbad]] = True
grow = ndi.binary_dilation(mask, iterations=2)
blur = ndi.gaussian_filter(out, (1.0, 1.0, 0))
out[grow] = blur[grow]
print('HEAD_PATCH flat triangles', len(flat), 'repainted', len(bad), 'texels', int(isbad.sum()))
vis = (img * 255).astype(np.uint8).copy(); vis[mask] = (255, 0, 255)
Image.fromarray(vis).resize((1024, 1024), Image.NEAREST).save('review/head_patch_mask.png')
if not DRY:
    Image.fromarray(np.uint8(np.clip(out, 0, 1) * 255 + 0.5)).save(OUT)
