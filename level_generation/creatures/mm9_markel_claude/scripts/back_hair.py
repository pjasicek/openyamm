#!/usr/bin/env python3
"""Back hair (mm9_markel, 2026-11-02): Smart Topology gave the hair shell a long tail hanging behind the neck onto the fur
mantle, and the 4K head retexture painted its lower half cream fur with a sharp edge to the copper hair: from behind it read
as a pale patch stuck to the hair (review/back_r1.png). MM9's Markel has copper hair down to the nape. Hair-shell texels on
the back (glTF z < 0.02) below 1.66 m that are fur-coloured (unsaturated and light) take the colour of the hair-shell
hair colour at the same luminance rank (a quantile ramp measured on the hair texels), so the fur paint's own strand detail
stays and only its colour changes; the membership is soft (saturation and lightness ramps, blurred 1.5 px), so no edge. Runs on textures/mk_tp_head_basecolor.png
in place after bald_crown.py (before spot_fix.py and hand_clean.py). Usage (project folder): back_hair.py [lift 0.10]"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from pygltflib import GLTF2
LIFT = float(sys.argv[1]) if len(sys.argv) > 1 else 0.10
T = 'textures/mk_tp_head_basecolor.png'
img = np.asarray(Image.open(T).convert('RGB')).astype(np.float64) / 255
N = img.shape[0]
g = GLTF2().load('work/mk_body_tex.glb'); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a.type]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a.componentType]
    return np.frombuffer(blob, dtype=dt, count=a.count * n, offset=(bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
prim = next(p for m in g.meshes for p in m.primitives if g.materials[p.material].name.startswith('MarkelHead'))
P = acc(prim.attributes.POSITION).astype(np.float64); UV = acc(prim.attributes.TEXCOORD_0).astype(np.float64)
I = acc(prim.indices).reshape(-1, 3).astype(np.int64)
_, weld = np.unique(np.round(P, 5), axis=0, return_inverse=True); weld = weld.ravel(); F = weld[I]; n = weld.max() + 1
r = np.concatenate([F[:, 0], F[:, 1], F[:, 2]]); c = np.concatenate([F[:, 1], F[:, 2], F[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
fp = lab[F[:, 0]]
parts = np.unique(fp)
hair = min(parts, key=lambda k: P[I[fp == k]].reshape(-1, 3)[:, 2].min())       # the part reaching furthest back
pos = np.full((N, N, 3), np.nan)
for f in np.where(fp == hair)[0]:
    tri = I[f]; uv = UV[tri] * N
    x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0 - 1, 0), min(x1 + 1, N)), np.arange(max(y0 - 1, 0), min(y1 + 1, N)))
    q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    a, b, cc = uv; m = np.array([[b[0] - a[0], cc[0] - a[0]], [b[1] - a[1], cc[1] - a[1]]])
    if xs.size == 0 or abs(np.linalg.det(m)) < 1e-12:
        continue
    l = np.linalg.solve(m, (q - a).T).T; w = np.column_stack([1 - l.sum(1), l]); ok = (w >= -0.03).all(1)
    pos[q[ok, 1].astype(int), q[ok, 0].astype(int)] = w[ok] @ P[tri]
cov = ~np.isnan(pos[..., 0])
mx, mn = img.max(2), img.min(2); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
lum = img @ np.array([0.299, 0.587, 0.114])
Y, Z = np.nan_to_num(pos[..., 1]), np.nan_to_num(pos[..., 2])
def smooth(x, lo, hi):
    t = np.clip((x - lo) / (hi - lo), 0, 1); return t * t * (3 - 2 * t)
# soft fur membership (unsaturated and light), on the back of the hair shell below the crown
zone = cov & (Z < 0.06) & (Y < 1.76)
# soft zone edges (hair reshape: a hard Y < 1.66 / Z < 0.02 cut drew a light U-shaped line across the back of the head)
zw = smooth(1.74 - Y, 0.0, 0.05) * smooth(0.04 - Z, 0.0, 0.04) * zone
mem = smooth(0.50 - sat, 0.0, 0.15) * smooth(lum, 0.38, 0.50) * zone
# neck-skin paint on the hair shell (Meshy painted the nape where the tail met the neck; after the reshape those faces sit on
# the back of the head as a light U-shaped band): skin = pinkish (blue channel well above the hair's), light
skin = smooth(img[..., 2] / np.maximum(img[..., 0], 1e-3), 0.36, 0.46) * smooth(lum, 0.40, 0.50) * zone
mem = np.maximum(mem, skin)
mem = ndi.gaussian_filter(ndi.maximum_filter(mem, 5), 1.5) * zw      # grown 2 px: the old fur edge left a pale rim
fur = mem > 0.5
hairtex = cov & (mem < 0.05) & (sat > 0.5) & (img[..., 0] > img[..., 1]) & (Y > 1.45) & (Z < 0.05)
# recolour by luminance quantile: a fur texel at luminance rank q takes the mean hair colour at the same rank among the hair
# texels (the fur paint's own strand structure stays, now copper; a 3D copy of strands from higher up was tried first and
# came out as a patchwork of chart-sized pieces, review/back_r2.png)
fl = np.sort(lum[fur]); hl = lum[hairtex]; hc = img[hairtex]
order = np.argsort(hl); hl, hc = hl[order], hc[order]
bins = 64
edges = np.linspace(0, len(hl), bins + 1).astype(int)
ramp = np.array([hc[edges[i]:edges[i + 1]].mean(0) for i in range(bins)])
q = np.searchsorted(fl, lum, side='left') / max(len(fl), 1)
rec = ramp[np.clip((q * bins).astype(int), 0, bins - 1)]
w = np.clip(mem, 0, 1)[..., None]
out = img * (1 - w) + rec * w
# the old fur edge carried a painted dark outline: lift the dark texels of a 6 px band round the membership edge to the local
# median luminance (colour kept), so the line goes and the strands stay
band = ndi.binary_dilation((mem > 0.05) & (mem < 0.95), iterations=5) & zone
lo = out @ np.array([0.299, 0.587, 0.114])
covf = zone.astype(float)
med = ndi.gaussian_filter(lo * covf, 5) / np.maximum(ndi.gaussian_filter(covf, 5), 1e-6)
gain = np.where(band, np.clip(med / np.maximum(lo, 1e-3), 0.7, 1.8), 1.0)   # dark outline and light rim both to the local median
gain = 1 + (ndi.gaussian_filter(gain, 1.0) - 1) * band
out = np.clip(out * gain[..., None], 0, 1)
# hair reshape (2026-11-02): the old fur edge left a tonal band across the back of the head; level the broad luminance of the
# back hair (Gaussian 12 px, normalised over the zone) to its median, fine strand detail kept, gain within 0.75-1.35
zb = cov & (Z < 0.03) & (Y < 1.72)
lb = out @ np.array([0.299, 0.587, 0.114]); zf = zb.astype(float)
lp = ndi.gaussian_filter(lb * zf, 12) / np.maximum(ndi.gaussian_filter(zf, 12), 1e-6)
tgt = np.median(lb[zb])
lev = np.clip(tgt / np.maximum(lp, 1e-3), 0.75, 1.35)
fz = np.clip(ndi.distance_transform_edt(zb) / 6.0, 0, 1)
out = np.clip(out * (1 + (lev - 1) * fz)[..., None], 0, 1)
dist, (iy, ix) = ndi.distance_transform_edt(~cov, return_indices=True)
gut = (~cov) & (dist <= 4) & ((mem[iy, ix] > 0.05) | zb[iy, ix])
out[gut] = out[iy[gut], ix[gut]]
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(T)
print('BACK_HAIR hair part', int(hair), 'fur texels repainted', int(fur.sum()), 'hair sources', int(hairtex.sum()), 'ramp lum', [round(float(x), 3) for x in (ramp @ np.array([0.299, 0.587, 0.114]))[[0, 32, 63]]])
