#!/usr/bin/env python3
"""One continuous skin tone over face, forehead, bald scalp, ears and neck (orchestrator review 2026-11-02: the face read
as a ruddier mask with a hard edge against the paler pink scalp and temples; MM9's crown is the same warm tone as the
face). Head texels (rest height > 0.85 m: the hand squares are left alone) classified as skin (warm hue, saturation
0.2-0.85, not dark, not the light low-saturation hair/beard/brows, not the blue/white eyes, not the lips) take their broad
colour from one target T while keeping the paint's own detail: out = img x T / lowpass(img), the low-pass a mask-normalised
Gaussian (SIGMA texels) over the skin only, applied with a feathered mask x STRENGTH. T defaults to the median of the
front-facing cheek/forehead skin moved HUE_MIX toward MM9 skin A's warm tan (by chromaticity, the luminance kept).
Reads textures/<prefix>_head_basecolor_preunify.png (written on the first run), writes <prefix>_head_basecolor.png.
Usage (project folder): skin_unify.py <export glb> <prefix> [--target r,g,b] [--sigma 28] [--strength 0.9]"""
import argparse, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
ap = argparse.ArgumentParser()
ap.add_argument('glb'); ap.add_argument('prefix')
ap.add_argument('--target', default=''); ap.add_argument('--sigma', type=float, default=28.0)
ap.add_argument('--strength', type=float, default=0.9); ap.add_argument('--hue-mix', type=float, default=0.35)
o = ap.parse_args()
f = Path(f'textures/{o.prefix}_head_basecolor.png'); bk = f.with_name(f.stem + '_preunify.png')
if not bk.exists():
    shutil.copyfile(f, bk)
img = np.asarray(Image.open(bk).convert('RGB'), float)
N = img.shape[0]
pos, cov = texel_positions(o.glb, 'PeasantDM4Head', N)
P = np.nan_to_num(pos); x, y, z = P[..., 0], P[..., 1], P[..., 2]
r, g, b = img[..., 0], img[..., 1], img[..., 2]
mx, mn = img.max(-1), img.min(-1)
sat = (mx - mn) / np.maximum(mx, 1)
lum = img @ [0.299, 0.587, 0.114]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
head = cov & (y > 0.85)
# loose parts of the head primitive (vertices welded by position): the hair is its own part, so it never counts as skin
from pygltflib import GLTF2
G = GLTF2().load(o.glb); blob = G.binary_blob()
def acc(i):
    a = G.accessors[i]; bv = G.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a.type]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32}[a.componentType]
    return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
pr = next(q for m in G.meshes for q in m.primitives if G.materials[q.material].name == 'PeasantDM4Head')
VP = acc(pr.attributes.POSITION); UVs = acc(pr.attributes.TEXCOORD_0); TR = acc(pr.indices).reshape(-1, 3).astype(int)
_, weld = np.unique(np.round(VP, 5), axis=0, return_inverse=True); weld = weld.ravel()
par = np.arange(weld.max() + 1)
def fnd(i):
    while par[i] != i:
        par[i] = par[par[i]]; i = par[i]
    return i
for t in TR:
    a_, b_, c_ = fnd(weld[t[0]]), fnd(weld[t[1]]), fnd(weld[t[2]])
    par[b_] = a_; par[fnd(c_)] = a_
comp = np.array([fnd(weld[t[0]]) for t in TR])
ids, cnt = np.unique(comp, return_counts=True)
order = ids[np.argsort(-cnt)]
cid = np.searchsorted(order, comp) if False else np.array([int(np.where(order == c)[0][0]) for c in comp])
# the hair part: the largest part whose triangles mostly sit above the eyes and behind the face
cy = VP[TR].mean(1)
hair_id = None
for k in range(len(order)):
    m = cid == k
    print('PART', k, int(m.sum()), 'median', np.median(cy[m], 0).round(3), 'min', cy[m].min(0).round(3), 'max', cy[m].max(0).round(3))
for k in range(min(6, len(order))):
    m = cid == k
    if m.sum() > 200 and np.median(cy[m, 1]) > 0.95 and np.median(cy[m, 2]) < 0.0:
        hair_id = k; break
partimg = -np.ones((N, N), int)
for ti, t in enumerate(TR):
    uv = UVs[t] * N
    x0, y0 = np.maximum(np.floor(uv.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(uv.max(0)).astype(int), N - 1)
    if x1 < x0 or y1 < y0:
        continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    A, B, C = uv
    den = (B[1] - C[1]) * (A[0] - C[0]) + (C[0] - B[0]) * (A[1] - C[1])
    if abs(den) < 1e-12:
        continue
    l0 = ((B[1] - C[1]) * (gx - C[0]) + (C[0] - B[0]) * (gy - C[1])) / den
    l1 = ((C[1] - A[1]) * (gx - C[0]) + (A[0] - C[0]) * (gy - C[1])) / den
    ins = (l0 >= -1e-3) & (l1 >= -1e-3) & (1 - l0 - l1 >= -1e-3)
    partimg[(gy[ins] - 0.5).astype(int), (gx[ins] - 0.5).astype(int)] = cid[ti]
hairpart = partimg == hair_id
print('HAIR part', hair_id, 'texels', int(hairpart.sum()), 'parts', len(order))
lips = (np.abs(x) < 0.035) & (y > 0.995) & (y < 1.035) & (z > 0.11)
beard = (y < 1.04) & (y > 0.95) & (z > -0.02)          # the beard and moustache hang from the shell below the cheeks
pale = (sat < 0.3) & (lum > 120)                        # brows, beard strands and stray hair on the shell
skin = head & ~hairpart & ~beard & ~pale & ((hue < 45) | (hue > 345)) & (sat > 0.2) & (sat < 0.85) & (lum > 70) & (r > g) & ~lips
skin = ndimage.binary_opening(skin, iterations=1)
front = skin & (z > 0.10) & (y > 1.03) & (y < 1.12)
if o.target:
    T = np.array([float(v) for v in o.target.split(',')])
else:
    T = np.median(img[front], 0)
    mm9 = np.array([180.0, 106.0, 61.0])                  # MM9 skin A face (warm tan), chromaticity only
    lt = T @ [0.299, 0.587, 0.114]
    tgt = mm9 * lt / (mm9 @ [0.299, 0.587, 0.114])
    T = T * (1 - o.hue_mix) + tgt * o.hue_mix
w0 = skin.astype(float)
den = ndimage.gaussian_filter(w0, o.sigma)
low = np.stack([ndimage.gaussian_filter(img[..., c] * w0, o.sigma) for c in range(3)], -1) / np.maximum(den, 1e-6)[..., None]
ratio = np.clip(T[None, None] / np.maximum(low, 1), 0.5, 2.0)
w = ndimage.gaussian_filter(w0, 2.0) * head * o.strength
out = img * (1 - w[..., None]) + np.clip(img * ratio, 0, 255) * w[..., None]
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
out[~cov] = out[iy[~cov], ix[~cov]]
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f)
sc = skin & (z < 0.08) & (y > 1.08)
print('SKIN_UNIFY', o.prefix, 'target', T.round(), 'skin texels', int(skin.sum()), 'front median before', np.median(img[front], 0).round(),
      'scalp/back median before', np.median(img[sc], 0).round() if sc.any() else None, 'after', np.median(out[front], 0).round(),
      np.median(out[sc], 0).round() if sc.any() else None)
