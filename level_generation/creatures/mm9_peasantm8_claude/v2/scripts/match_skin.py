#!/usr/bin/env python3
"""Skin tone of a new body paint matched to the approved one (texture pass 2026-10-30, Forad): the 4K retexture
painted the bare arms darker than the approved v1 paint (rendered upper arm 124/79/53 against 145/88/55), while the
face and the hands (head set, graded to the v1 body skin by compose_headhand.py) keep the approved tone, so the
wrists would show a seam. The approved graded colour is resampled onto the new layout at the same surface points
(uv_pairs.py), and inside the new paint's skin (class 1 of compose_texpass.py, softened 2 px) the new colour takes
the broad difference to it: new + blur(old - new), a mask-normalised Gaussian of SIGMA texels, so the tone follows
the approved paint region by region while the detail (and the absence of the old blotches) stays the new paint's.
Run once after grade_basecolor.py; reads the ungraded-name input and writes the output path.

Usage: match_skin.py <new graded png> <new classes png> <old graded png> <uv pairs npz> <out png> [sigma 40]"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

new_p, new_c, old_p, pairs_p, out_p = sys.argv[1:6]
SIGMA = float(sys.argv[6]) if len(sys.argv) > 6 else 40.0
new = np.asarray(Image.open(new_p).convert('RGB'), np.float32)
old = np.asarray(Image.open(old_p).convert('RGB'), np.float32)
N = new.shape[0]
pairs = np.load(pairs_p)
remap = np.zeros_like(new)
cover = np.zeros(new.shape[:2], bool)


def bilinear(img, u, v):
    H, W = img.shape[:2]
    x, y = u * W - 0.5, (1 - v) * H - 0.5
    x0, y0 = np.clip(np.floor(x).astype(int), 0, W - 2), np.clip(np.floor(y).astype(int), 0, H - 2)
    fx, fy = np.clip(x - x0, 0, 1)[:, None], np.clip(y - y0, 0, 1)[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


for to, tn in zip(pairs['old'], pairs['new']):
    p = np.stack([tn[:, 0] * N, (1 - tn[:, 1]) * N], 1)            # texel space (row 0 = v 1)
    lo, hi = np.floor(p.min(0)).astype(int), np.ceil(p.max(0)).astype(int) + 1
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], N)), np.arange(max(lo[1], 0), min(hi[1], N)))
    if not xs.size:
        continue
    q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    T = np.array([p[1] - p[0], p[2] - p[0]]).T
    if abs(np.linalg.det(T)) < 1e-9:
        continue
    st = (q - p[0]) @ np.linalg.inv(T).T
    w = np.stack([1 - st.sum(1), st[:, 0], st[:, 1]], 1)
    inside = (w >= -0.01).all(1)
    if not inside.any():
        continue
    w = w[inside]
    uv = w @ to
    yy, xx = ys.ravel()[inside], xs.ravel()[inside]
    remap[yy, xx] = bilinear(old, uv[:, 0], uv[:, 1])
    cover[yy, xx] = True
skin = np.asarray(Image.open(new_c).resize((N, N), Image.NEAREST)) == 1
m = (skin & cover).astype(np.float32)
diff = (remap - new) * m[..., None]
den = ndimage.gaussian_filter(m, SIGMA)
broad = np.stack([ndimage.gaussian_filter(diff[..., k], SIGMA) for k in range(3)], -1) / np.maximum(den, 1e-4)[..., None]
soft = np.clip(ndimage.gaussian_filter(skin.astype(np.float32), 2.0), 0, 1)[..., None]
out = np.clip(new + broad * soft, 0, 255)
Image.fromarray(out.round().astype(np.uint8)).save(out_p)
sk = skin & cover
print('MATCH_SKIN', out_p, 'skin texels', int(sk.sum()), 'mean new', new[sk].mean(0).round(1).tolist(),
      'approved here', remap[sk].mean(0).round(1).tolist(), 'out', out[sk].mean(0).round(1).tolist())
