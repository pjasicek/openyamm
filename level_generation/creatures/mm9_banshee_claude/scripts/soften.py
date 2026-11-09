#!/usr/bin/env python3
"""The sleeves toward MM9, on the shared paint, no repaint: MM9's are plain gold-brown with a light trim; Meshy's gauntlets read as black-and-white leopard print close up. Local contrast cut on sleeves and gauntlets, colour pulled toward MM9's gold-brown, the cuff ruffle left alone. The bodice's gold bands get the same at half strength. Overwrites textures/banshee_basecolor_graded.png. Run from the project folder after the grade."""
import numpy as np
from PIL import Image
from scipy import ndimage
SIZE = 2048
p = 'textures/banshee_basecolor_graded.png'
im = np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
d = np.load('work/uv_v1.npz')
idx, uv, co, part = d['Body_idx'], d['Body_uv'].copy(), d['Body_co'], d['Body_part']
uv[..., 1] = 1 - uv[..., 1]
P = np.zeros((SIZE // 2, SIZE // 2, 3), np.float32); kind = np.zeros((SIZE // 2, SIZE // 2), np.int8)
S2 = SIZE // 2
for f in np.where(part == 0)[0]:
    t = uv[f] * S2
    lo = np.floor(t.min(0)).astype(int) - 1; hi = np.ceil(t.max(0)).astype(int) + 2
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], S2)), np.arange(max(lo[1], 0), min(hi[1], S2)))
    if xs.size == 0:
        continue
    mt = np.array([t[1] - t[0], t[2] - t[0]]).T
    if abs(np.linalg.det(mt)) < 1e-9:
        continue
    st = (np.stack([xs + 0.5, ys + 0.5], -1) - t[0]) @ np.linalg.inv(mt).T
    ok = (st[..., 0] >= -0.03) & (st[..., 1] >= -0.03) & (st.sum(-1) <= 1.06)
    w = st[ok]; b0 = 1 - w[:, 0] - w[:, 1]
    v = idx[f]
    P[ys[ok], xs[ok]] = b0[:, None] * co[v[0]] + w[:, 0:1] * co[v[1]] + w[:, 1:2] * co[v[2]]
    kind[ys[ok], xs[ok]] = 1
x, y, z = P[..., 0], P[..., 1], P[..., 2]
ax = np.abs(x)
upper = kind == 1
arm = upper & (ax > 0.215)
# ruffle at the wrist: the last 4 cm of the sleeve
ruff = upper & (ax > 0.565)
band = upper & (ax < 0.18) & (y < -0.09) & (z > 0.2)
mask = ndimage.gaussian_filter((arm & ~ruff).astype(np.float32), 2.0)
mb = ndimage.gaussian_filter(band.astype(np.float32), 2.0)
mask = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.BILINEAR), np.float32) / 255
mb = np.asarray(Image.fromarray((mb * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.BILINEAR), np.float32) / 255
L = im @ np.array([0.3, 0.59, 0.11], np.float32)
sup = (mask > 0.01) | (mb > 0.01)
w = ndimage.gaussian_filter(sup.astype(np.float32), 16)
low = ndimage.gaussian_filter(L * sup, 16) / np.maximum(w, 1e-3)
GOLD = np.array([0.80, 0.63, 0.40], np.float32)     # MM9's sleeve, read off bansheeA
gold = GOLD / (GOLD @ np.array([0.3, 0.59, 0.11], np.float32))


def apply(rgb, keep, tint, m):
    L1 = low + (L - low) * keep
    L1 = L1 * 0.5 + (low.clip(0.32, 0.62)) * 0.5 + (L1 - low) * 0.5     # the means of the print's patches drift to a mid gold
    out = rgb * (L1 / np.maximum(L, 1e-3))[..., None]
    out = out * (1 - tint) + L1[..., None] * gold * tint
    return rgb * (1 - m[..., None]) + out * m[..., None]


res = apply(im, 0.34, 0.6, mask)
res = apply(res, 0.62, 0.25, mb)
Image.fromarray((np.clip(res, 0, 1) * 255 + 0.5).astype(np.uint8)).save(p)
print('SOFTEN arm %.3f band %.3f' % (float((mask > 0.5).mean()), float((mb > 0.5).mean())))
