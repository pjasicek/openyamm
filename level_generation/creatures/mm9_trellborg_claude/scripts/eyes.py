#!/usr/bin/env python3
"""The eyeballs are painted from their own 3D position, not projected: Codex's irises drift a few pixels off the clay's eyes (Honk's lesson) and they stay out of the region mask, so all tiers share them. In place on textures/gezz_head_final.png."""
import numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage
Z = np.load('work/head_pos.npz'); pos, cov, prt = Z['pos'], Z['cov'], Z['prt']
im = np.asarray(Image.open('textures/gezz_head_final.png').convert('RGB'), np.float32) / 255
# texels no view saw (under the chin, under the mane) hold a nearest-colour smear: fur grain from the body paint's own high band
seen = np.load('work/head_seen.npy')
B = np.asarray(Image.open('textures/gezz_body_final.png').convert('L').resize(im.shape[:2][::-1]), np.float32) / 255
hp = B - ndimage.gaussian_filter(B, 7)
hp = np.roll(hp, (311, 173), (0, 1))
u = ~seen & cov
f = ndimage.gaussian_filter(u.astype(np.float32), 3)[..., None]
im = np.clip(im * (1 + np.clip(hp, -0.2, 0.2)[..., None] * 3.0 * f), 0, 1)
print('UNSEEN', float(u.mean()))
m = prt == 13
P = pos[m]
out = np.zeros_like(P)
for sg in (1, -1):
    e = (P[:, 0] * sg > 0)
    c = np.array([sg * P[e, 0].__abs__().mean(), P[e, 1].max() - 0.5 * np.ptp(P[e, 1]), P[e, 2].mean()])
    c = 0.5 * (P[e].min(0) + P[e].max(0))
    fwd = np.array([sg * 0.06, -1.0, 0.0]); fwd /= np.linalg.norm(fwd)
    d = P[e] - c; d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-6)
    a = np.degrees(np.arccos(np.clip(d @ fwd, -1, 1)))
    print('EYE', sg, np.round(c, 3), 'r', np.round(np.ptp(P[e], 0) / 2, 3))
    sclera = np.array([0.62, 0.46, 0.30]); ir0 = np.array([0.95, 0.52, 0.06]); ir1 = np.array([0.55, 0.16, 0.02]); pupil = np.array([0.012, 0.01, 0.008])
    t = np.clip(a / 26, 0, 1)[:, None]
    col = ir0 * (1 - t) + ir1 * t
    col = np.where((a > 26)[:, None], sclera * (1 - np.clip((a - 26) / 50, 0, 0.6))[:, None], col)
    ring = np.clip(1 - np.abs(a - 26) / 2.5, 0, 1)[:, None]
    col = col * (1 - ring * 0.8) + 0.02 * ring
    pu = np.clip((11 - a) / 1.5, 0, 1)[:, None]
    col = col * (1 - pu) + pupil * pu
    out[e] = col
res = im.copy(); res[m] = out
# teeth: ivory, the paint's shading kept as a share; Codex's drift left gum colours on them
t = prt == 14
F = np.load('work/faces.npz'); tc = F['hc'][F['hp'] == 14]
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
V, inv = np.unique(np.round(tc.reshape(-1, 3), 5), axis=0, return_inverse=True); inv = inv.ravel().reshape(-1, 3)
n_, lab = connected_components(coo_matrix((np.ones(len(inv) * 2), (np.r_[inv[:, 0], inv[:, 1]], np.r_[inv[:, 1], inv[:, 2]])), shape=(len(V), len(V))), directed=False)
cen = np.array([V[lab == i].mean(0) for i in range(n_)]); ext = np.array([np.ptp(V[lab == i], 0) for i in range(n_)])
print('TEETH', n_)
Pt = pos[t]
k = np.argmin(((Pt[:, None] - cen[None]) ** 2).sum(2), 1)
r = np.linalg.norm((Pt - cen[k]) / np.maximum(ext[k] * [0.5, 0.5, 0.5], 1e-4) * [1, 0.3, 1], axis=1)
L = (im @ np.array([0.2126, 0.7152, 0.0722], np.float32))[t]
res[t] = np.array([0.88, 0.80, 0.62], np.float32) * (np.clip(0.75 + L * 0.5, 0.6, 1.0) * np.clip(1.05 - 0.75 * r ** 3, 0.12, 1))[:, None]
# the shell's sheaths round the tusks and teeth, warm like them
x, y, z = np.abs(pos[..., 0]), pos[..., 1], pos[..., 2]
lum = im @ np.array([0.2126, 0.7152, 0.0722], np.float32); sat = (im.max(2) - im.min(2)) / np.maximum(im.max(2), 1e-6)
iv = cov & (prt < 13) & (x < 0.14) & (y < -0.25) & (z > 0.74) & (z < 0.845) & (lum > 0.3) & (sat < 0.55)
iv = ndimage.binary_closing(iv, iterations=2) & cov
res[iv] = np.array([0.88, 0.80, 0.62], np.float32) * np.clip(lum[iv] * 1.15, 0.2, 1.0)[:, None]
res = np.where(ndimage.binary_dilation(m, iterations=2)[..., None] & ~m[..., None], res, res)
idx = ndimage.distance_transform_edt(~m, return_distances=False, return_indices=True)
near = ndimage.binary_dilation(m, iterations=3) & ~cov
res[near] = res[idx[0][near], idx[1][near]]
Image.fromarray((np.clip(res, 0, 1) * 255 + .5).astype('u1')).save('textures/gezz_head_final.png')
print('EYES done', int(m.sum()))
