#!/usr/bin/env python3
"""Dark specks under the eyes (mm9_markel, 2026-11-02): the 4K head retexture left a small dark brown triangle about 1 cm
under each eye (a UV-seam speck; it reads as a mole or a dark nostril-like mark in close-ups). Face texels in a box under
each eye (to the lower lid) that are beard-brown (saturated, warm) and darker than SPOT x the local median (Gaussian 6 px) are dilated by 2 px and refilled from the
surrounding skin by normalised convolution, feathered 2 px. Runs on textures/pm5_tp_head_basecolor.png in place, after
bald_crown.py and before hand_clean.py. Box in glTF bind coordinates (work/pm5_body_tex.glb). Usage: spot_fix.py [spot 0.82]"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from pygltflib import GLTF2
SPOT = float(sys.argv[1]) if len(sys.argv) > 1 else 0.82
import os
T = os.environ.get('HEADTEX_PNG', 'textures/pm5_tp_head_basecolor.png')
img = np.asarray(Image.open(T).convert('RGB')).astype(np.float64) / 255
N = img.shape[0]
g = GLTF2().load('work/pm5_body_tex.glb'); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a.type]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a.componentType]
    return np.frombuffer(blob, dtype=dt, count=a.count * n, offset=(bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
prim = next(p for m in g.meshes for p in m.primitives if g.materials[p.material].name.startswith('PeasantM5Head'))
P = acc(prim.attributes.POSITION).astype(np.float64); UV = acc(prim.attributes.TEXCOORD_0).astype(np.float64)
I = acc(prim.indices).reshape(-1, 3).astype(np.int64)
pos = np.full((N, N, 3), np.nan)
cen = P[I].mean(1)
for f in np.where((cen[:, 1] > 1.58) & (cen[:, 1] < 1.66) & (cen[:, 2] > 0.04))[0]:
    tri = I[f]; uv = UV[tri] * N
    x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)), np.arange(max(y0, 0), min(y1, N)))
    q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    a, b, c = uv; m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
    if xs.size == 0 or abs(np.linalg.det(m)) < 1e-12:
        continue
    l = np.linalg.solve(m, (q - a).T).T; w = np.column_stack([1 - l.sum(1), l]); ok = (w >= -0.02).all(1)
    pos[q[ok, 1].astype(int), q[ok, 0].astype(int)] = w[ok] @ P[tri]
cov = ~np.isnan(pos[..., 0]); X, Y, Z = (np.nan_to_num(pos[..., k]) for k in range(3))
cx = float(np.median(P[:, 0][P[:, 1] > 1.6]))
box = cov & (Y > 1.608) & (Y < 1.650) & (np.abs(X - cx) > 0.012) & (np.abs(X - cx) < 0.062) & (Z > 0.05)
lum = img @ np.array([0.299, 0.587, 0.114])
covf = cov.astype(float)
med = ndi.gaussian_filter(lum * covf, 6) / np.maximum(ndi.gaussian_filter(covf, 6), 1e-6)
mxc, mnc = img.max(2), img.min(2)
sat = np.where(mxc > 0, (mxc - mnc) / np.maximum(mxc, 1e-6), 0)
# beard-brown texels only (warm, saturated, darker than the skin round them); lashes are grey-blue and stay
spot = box & (lum < SPOT * med) & (sat > 0.5) & (img[..., 0] > img[..., 1]) & (img[..., 1] > img[..., 2])
spot = ndi.binary_dilation(spot, iterations=2) & cov
import os
if os.environ.get('NO_GENERIC'):   # mm9_peasantm5: brown irises read as beard-brown specks; only the lash-line sliver below
    spot[:] = False
known = (cov & ~spot).astype(float)
est = img.copy(); done = ~spot
for sg in (2, 4, 8):
    ws = ndi.gaussian_filter(known, sg); val = ndi.gaussian_filter(img * known[..., None], (sg, sg, 0)) / np.maximum(ws, 1e-6)[..., None]
    take = (~done) & (ws > 0.05); est[take] = val[take]; done |= take
al = np.clip(ndi.distance_transform_edt(spot) / 2.0, 0, 1)
out = img * (1 - al[..., None]) + est * al[..., None]
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(T)
# explicit UV triangles (image px, y down) found by head_closeups.py IDMODE probes: face 5653 of the LOD0 head primitive under
# the right eye maps onto Meshy's lash line of the neighbouring lid (a 10 px UV sliver of an 8 mm triangle): it reads as a dark
# triangle. Its texels (dilated 1 px) take the skin of the 3D-nearest texels of the other faces round it.
TRIS = [([(916, 427), (929, 433), (925, 424)], (-0.023, 1.642, 0.083))]   # under the right eye: lash-line sliver
# (a faint lighter triangle beside the nose, face 4597 UV (851,863)-(826,881)-(824,859), was tried too: its 3D neighbours
# include the nostril shadow and it came out darker and more visible, so it keeps Meshy's paint)
yy, xx = np.mgrid[0:N, 0:N]
for tri, c3 in TRIS:
    a, b, c = (np.array(t, float) for t in tri)
    m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
    q = np.stack([xx.ravel() + 0.5 - a[0], yy.ravel() + 0.5 - a[1]])
    l = np.linalg.solve(m, q).T
    inside = ((l >= -0.05).all(1) & (l.sum(1) <= 1.05)).reshape(N, N)
    inside = ndi.binary_dilation(inside, iterations=1)
    # the skin round the triangle ON THE SURFACE (texels of other faces within 1.4 cm of its centroid); a UV-space ring
    # samples the neighbouring lid and lash paint and came out too dark
    rl = out @ np.array([0.299, 0.587, 0.114])
    mxr, mnr = out.max(2), out.min(2); sr = (mxr - mnr) / np.maximum(mxr, 1e-6)
    near = cov & ~inside & (np.linalg.norm(np.nan_to_num(pos) - np.array(c3), axis=2) < 0.02)
    if os.environ.get('NO_GENERIC'):   # mm9_peasantm5: skin texels only (the eye whites beside the lid made the fill pale)
        near &= (rl < 0.9) & (rl > 0.3) & (np.nan_to_num(pos[..., 1]) < c3[1] - 0.001)   # skin below the lower lid only
        near &= np.linalg.norm(np.nan_to_num(pos) - np.array(c3), axis=2) < float(os.environ.get('NEAR_R', '0.02'))
    # each texel takes the colour of the 3D-nearest texel of the OTHER faces round it (the skin that is really there; a flat
    # median of the neighbourhood came out darker or lighter than the cheek right beside it), averaged over 6 neighbours
    from scipy.spatial import cKDTree
    src = np.argwhere(near); dst = np.argwhere(inside & cov)
    tree = cKDTree(pos[near])
    _, k = tree.query(pos[inside & cov], k=6)
    col = out[src[:, 0], src[:, 1]][k].mean(1)
    out[dst[:, 0], dst[:, 1]] = col
    col = col.mean(0)
    print('SPOT_FIX triangle', tri, 'texels', int(inside.sum()), 'near', int(near.sum()), 'colour', (col * 255).round().tolist())
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(T)
lab, n = ndi.label(spot)
print('SPOT_FIX texels', int(spot.sum()), 'blobs', n, 'box', int(box.sum()))
