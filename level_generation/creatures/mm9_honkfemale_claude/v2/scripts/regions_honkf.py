#!/usr/bin/env python3
"""Body region mask and tier ramps, female Honk (one body paint; run from the project folder).
Region: R trim (the knot bands, ramped to MM9's olive). Her two tiers differ only in the head.
Writes textures/honkf_region_mask.png, textures/honkf_ramps.json, review/region_mask.png."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path('..').resolve() / 'claude_shared'))
import region_variants as RV
S = 1024
base = np.asarray(Image.open('textures/honkf_basecolor_graded.png').convert('RGB').resize((S, S), Image.LANCZOS), np.float64) / 255
D = np.load('v2/work/uv_body.npz')
# texel xyz
xyz = np.zeros((S, S, 3), np.float32); cov = np.zeros((S, S), bool)
for uv, x, h, k in zip(D['uv'], D['xyz'], D['head'], D['hand']):
    if h or k:
        continue
    p = uv * S; p[:, 1] = S - p[:, 1]
    lo = np.floor(p.min(0)).astype(int); hi = np.ceil(p.max(0)).astype(int) + 1
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], S)), np.arange(max(lo[1], 0), min(hi[1], S)))
    if xs.size == 0:
        continue
    q = np.stack([xs + .5, ys + .5], -1)
    T = np.array([p[1] - p[0], p[2] - p[0]]).T
    if abs(np.linalg.det(T)) < 1e-9:
        continue
    st = (q - p[0]) @ np.linalg.inv(T).T
    inside = (st[..., 0] >= -.02) & (st[..., 1] >= -.02) & (st.sum(-1) <= 1.02)
    w = np.stack([1 - st.sum(-1), st[..., 0], st[..., 1]], -1)
    xyz[ys[inside], xs[inside]] = (w[inside] @ x)
    cov[ys[inside], xs[inside]] = True
mx, mn = base.max(2), base.min(2)
sat = (mx - mn) / np.maximum(mx, 1e-6)
r, g, b = base[..., 0], base[..., 1], base[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
lum = base @ np.array([.299, .587, .114])
trim = cov & (hue > 40) & (hue < 80) & (sat > .3)
trim = ndimage.binary_opening(trim, iterations=1)
linen = cov & (sat < .36) & (lum > .38) & (hue > 15) & (hue < 75) & ~trim
robe = np.zeros_like(linen)
def soft(m):
    idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
    a = np.float32(m)
    a = a[idx[0], idx[1]]                 # pad into the gutters like the colour
    return ndimage.gaussian_filter(a, 1.0)
chest = cov & (xyz[..., 2] > 0.38) & (xyz[..., 2] < 0.56) & (np.abs(xyz[..., 0]) < 0.1) & (xyz[..., 1] < 0.02) & (hue > 5) & (hue < 36) & (sat > 0.33) & (lum > .35)
mask = np.stack([soft(trim), soft(chest), np.zeros((S, S)), np.zeros((S, S))], -1)
Image.fromarray(np.uint8(np.clip(mask, 0, 1) * 255), 'RGBA').save('textures/honkf_region_mask.png')
Image.fromarray(np.uint8(np.clip(mask[..., :3], 0, 1) * 255)).save('review/region_mask.png')
LUMA = np.array([.2126, .7152, .0722])
def lin(a):
    a = np.asarray(a, np.float64)
    return np.where(a <= .04045, a / 12.92, ((a + .055) / 1.055) ** 2.4)
def sample_skin(name, test):
    px = np.asarray(Image.open(name).convert('RGB'), np.float64) / 255
    mx, mn = px.max(2), px.min(2); sat = (mx - mn) / np.maximum(mx, 1e-6)
    r, g, b = px[..., 0], px[..., 1], px[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    return lin(px[test(px, hue, sat)])
def ramp(region, target=None):
    """16 stops: base luminance range of the region -> quantiles of the target's linear colours (target None: the base's
    own mean colour per luminance band, tier A)."""
    L = lin(base)[region]; Y = L @ LUMA
    lo, hi = np.percentile(Y, 1.5), np.percentile(Y, 98.5)
    edges = np.linspace(lo, hi, 16)
    cols = []
    for k, e in enumerate(edges):
        w = np.exp(-((Y - e) / (hi - lo) * 12) ** 2)
        cols.append((L * w[:, None]).sum(0) / max(w.sum(), 1e-6))
    cols = np.array(cols)
    if target is not None:
        Yt = target @ LUMA
        ord_t = target[np.argsort(Yt)]
        # the region's luminance quantile at each stop -> the target's colour at that quantile (band mean)
        qs = np.searchsorted(np.sort(Y), edges) / len(Y)
        out = []
        for q in qs:
            a, b = int(max(q - .04, 0) * len(ord_t)), int(min(q + .04, 1) * len(ord_t)) + 1
            out.append(ord_t[a:b].mean(0))
        cols = np.array(out)
    return {'range': [float(max(lo, 1e-3)), float(min(hi, 1))], 'colors': np.clip(cols, 0, 1).round(5).tolist()}
olive = sample_skin('work/refs/HONKF1.png', lambda p, h, s: (h > 42) & (h < 75) & (s > .35))
print('olive', len(olive), olive.mean(0))
hd = np.asarray(Image.open('v2/textures/honkf_head_basecolor.png').convert('RGB'), np.float64) / 255
sk = lin(np.array([214, 158, 120.]) / 255 * np.linspace(.85, 1.08, 40)[:, None])
blue = lin(np.array([70, 88, 112.]) / 255 * np.linspace(.9, 1.1, 40)[:, None])
print('chest', int(chest.sum()), 'skin', sk.mean(0))
tiers = {'honkf_a': [ramp(trim, olive), ramp(chest, sk)], 'honkf_b': [ramp(trim, olive), ramp(chest, blue)]}
json.dump({'variants': list(tiers), 'materials': [{'base': 'HonkF', 'prefix': 'HonkF', 'mask': 'honkf_region_mask.png', 'ramps': tiers}]},
          open('textures/honkf_ramps.json', 'w'), indent=1)
print('REGIONS trim', int(trim.sum()))
