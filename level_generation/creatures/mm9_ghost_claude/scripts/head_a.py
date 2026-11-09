#!/usr/bin/env python3
"""Shadow's face, without a third retexture (budget): MM9's GHOST1 is a smooth plaster mask with black hollows, so it comes from the Apparition paint on the same head: wrinkles and colour flattened to a pale
blue-white, hair kept as fine lines, eye sockets and mouth painted black by 3D position (eyes found from the green irises, mouth from the dark cavity). Writes textures/ghost_head_a_graded.png."""
import numpy as np
from PIL import Image
from scipy import ndimage
S = 1024
d = np.load('work/uv_v1.npz')
idx, uv, co = d['Head_idx'], d['Head_uv'].copy(), d['Head_co']
uv[..., 1] = 1 - uv[..., 1]
b = np.asarray(Image.open('textures/ghost_head_b_graded.png').convert('RGB'), np.float32) / 255
P = np.zeros((S, S, 3), np.float32); seen = np.zeros((S, S), bool); inner = np.zeros((S, S), bool)
cen_ = 0.5 * (co.min(0) + co.max(0))
for f in range(len(idx)):
    t = uv[f] * S
    lo = np.floor(t.min(0)).astype(int) - 1; hi = np.ceil(t.max(0)).astype(int) + 2
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], S)), np.arange(max(lo[1], 0), min(hi[1], S)))
    if xs.size == 0:
        continue
    mt = np.array([t[1] - t[0], t[2] - t[0]]).T
    if abs(np.linalg.det(mt)) < 1e-10:
        continue
    st = (np.stack([xs + 0.5, ys + 0.5], -1) - t[0]) @ np.linalg.inv(mt).T
    ok = (st[..., 0] >= -0.03) & (st[..., 1] >= -0.03) & (st.sum(-1) <= 1.06)
    if not ok.any():
        continue
    w = st[ok]; b0 = 1 - w[:, 0] - w[:, 1]; v = idx[f]
    P[ys[ok], xs[ok]] = b0[:, None] * co[v[0]] + w[:, 0:1] * co[v[1]] + w[:, 1:2] * co[v[2]]
    seen[ys[ok], xs[ok]] = True
    v_ = co[idx[f]]
    inner[ys[ok], xs[ok]] = np.cross(v_[1] - v_[0], v_[2] - v_[0]) @ (v_.mean(0) - cen_) < 0
_, (iy, ix) = ndimage.distance_transform_edt(~seen, return_indices=True)
P = P[iy, ix]
x, y, z = P[..., 0], P[..., 1], P[..., 2]
b = np.asarray(Image.open('textures/ghost_head_b_graded.png').convert('RGB'), np.float32) / 255
L = b @ np.array([0.3, 0.59, 0.11])
sat = (b.max(2) - b.min(2)) / np.maximum(b.max(2), 1e-3)
front = y < np.percentile(y[seen], 40)
green = seen & (b[..., 1] > b[..., 0] * 1.5) & (b[..., 1] > b[..., 2] * 1.5) & (b[..., 1] > 0.3) & front
ex = {}
for s in (1, -1):
    m = green & (x * s > 0.005)
    ex[s] = (float(x[m].mean()), float(z[m].mean()))
print('EYES', ex, green.sum())
dark = seen & front & (L < 0.13) & (z < min(ex[1][1], ex[-1][1]) - 0.03) & (np.abs(x) < 0.06)
mc = (float(np.median(x[dark])), float(np.median(z[dark])))
mr = (float(np.percentile(np.abs(x[dark] - mc[0]), 96)), float(np.percentile(np.abs(z[dark] - mc[1]), 96)))
print('MOUTH', mc, mr, dark.sum())
blur = ndimage.gaussian_filter(L, 9)
detail = L - blur
# hair: brighter, bluer and behind the face line; the face keeps almost none of its wrinkles
face = np.clip((np.percentile(y[seen], 58) - y) / 0.03, 0, 1) * np.clip((0.078 - np.abs(x)) / 0.012, 0, 1)
tone = blur * 0.55 + 0.5 + detail * (0.18 * face + 0.9 * (1 - face))
tone = np.clip(tone, 0, 1)
lo, hi = np.array([120, 148, 152], np.float32) / 255, np.array([238, 247, 248], np.float32) / 255
A = lo + (hi - lo) * tone[..., None]
for s in (1, -1):
    # hollow sockets: soft black
    e = np.sqrt(((x - ex[s][0]) / 0.0185) ** 2 + ((z - ex[s][1]) / 0.0165) ** 2)
    k = np.clip((1.25 - e) / 0.5, 0, 1) * front
    k = k * k * (3 - 2 * k)
    A = A * (1 - k[..., None]) + np.array([0.02, 0.025, 0.03]) * k[..., None]
    ring = np.clip((1.9 - e) / 0.7, 0, 1) * (1 - k) * front * 0.45
    A = A * (1 - ring[..., None]) + np.array([0.34, 0.42, 0.45]) * ring[..., None]
e = np.sqrt(((x - mc[0]) / (mr[0] * 1.02)) ** 2 + ((z - mc[1]) / (mr[1] * 1.1)) ** 2)
k = np.clip((1.12 - e) / 0.3, 0, 1) * front
k = k * k * (3 - 2 * k)
A = A * (1 - k[..., None]) + np.array([0.012, 0.015, 0.02]) * k[..., None]
# the mouth is a black hollow on this tier: everything behind the lips, teeth too
wide = np.sqrt(((x - mc[0]) / (mr[0] * 1.5)) ** 2 + ((z - mc[1]) / (mr[1] * 1.5)) ** 2) < 1
lip_y = np.percentile(y[seen & wide & front], 4)
k = np.clip((y - (lip_y + 0.006)) / 0.004, 0, 1) * wide * front * ndimage.gaussian_filter(inner[iy, ix].astype(np.float32), 1.5)     # faces turned inward: the cavity, not the cheek beside it
A = A * (1 - k[..., None]) + np.array([0.012, 0.015, 0.02]) * k[..., None]
Image.fromarray((A.clip(0, 1) * 255).astype(np.uint8)).save('textures/ghost_head_a_graded.png')
# eye glow mask, the irises of Apparition and Specter (their paint sits at nearly the same texels)
c = np.asarray(Image.open('textures/ghost_head_c_graded.png').convert('RGB'), np.float32) / 255
blue = seen & (c[..., 2] > c[..., 0] * 1.5) & (c[..., 2] > 0.3) & front
m = ndimage.gaussian_filter((green | blue).astype(np.float32), 1.2)
near = np.zeros_like(m, bool)
for s in (1, -1):
    near |= np.sqrt((x - ex[s][0]) ** 2 + (z - ex[s][1]) ** 2) < 0.03
Image.fromarray((np.clip(m * near * 1.6, 0, 1) * 255).astype(np.uint8)).save('textures/ghost_eye_mask.png')
print('HEAD A done')
