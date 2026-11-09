#!/usr/bin/env python3
"""Body region mask and tier ramps, male Honk (one body paint; run from the project folder).
Regions: R robe (linen below the yoke line and the sleeves: the Seer's blue), G trim (all olive knot bands, ramped to MM9's
olive on every tier). The yoke is the linen reached from the chest in 3D without crossing a trim band (texel positions in
8 mm voxels), so it keeps its cream on the Seer as in MM9's HONKLEADER skin.
Writes textures/honkm_region_mask.png, textures/honkm_ramps.json, review/region_mask.png."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path('..').resolve() / 'claude_shared'))
import region_variants as RV
S = 1024
base = np.asarray(Image.open('textures/honkm_basecolor_graded.png').convert('RGB').resize((S, S), Image.LANCZOS), np.float64) / 255
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
trim = cov & (hue > 42) & (hue < 80) & (sat > .33)
trim = ndimage.binary_opening(trim, iterations=1)
linen = cov & (sat < .36) & (lum > .38) & (hue > 15) & (hue < 75) & ~trim
# voxels
V = 0.008
ijk = np.floor(xyz / V).astype(np.int32)
o = ijk[cov].min(0) - 2
dim = ijk[cov].max(0) - o + 3
vol = np.zeros(dim, np.uint8)            # 1 surface, 2 barrier
c = ijk - o
vol[c[cov][:, 0], c[cov][:, 1], c[cov][:, 2]] = 1
tv = np.zeros(dim, bool); tv[c[trim][:, 0], c[trim][:, 1], c[trim][:, 2]] = True
tv = ndimage.binary_dilation(tv, iterations=1)
surf = (vol == 1) & ~tv
lab, n = ndimage.label(surf, structure=np.ones((3, 3, 3)))
seed = [np.array(s) for s in ((0.03, -0.10, 0.54), (-0.05, -0.10, 0.54), (0.0, 0.17, 0.58))]
ids = set()
for s in seed:
    p = np.floor(s / V).astype(int) - o
    box = lab[p[0] - 3:p[0] + 4, p[1] - 3:p[1] + 4, p[2] - 3:p[2] + 4]
    ids |= set(np.unique(box[box > 0]).tolist())
print('flood ids', ids, [int((lab == i).sum()) for i in ids], 'of', n, int(surf.sum()))
yv = np.isin(lab, list(ids))
yv = ndimage.binary_dilation(yv, iterations=1)
yoke = np.zeros((S, S), bool)
yoke[cov] = yv[c[cov][:, 0], c[cov][:, 1], c[cov][:, 2]]
robe = linen & ~yoke
def soft(m):
    idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
    a = np.float32(m)
    a = a[idx[0], idx[1]]                 # pad into the gutters like the colour
    return ndimage.gaussian_filter(a, 1.0)
mask = np.stack([soft(robe), soft(trim & ~yoke | trim), np.zeros((S, S)), np.zeros((S, S))], -1)
RV.write_mask([mask[..., i] for i in range(2)] if False else mask, 'textures/honkm_region_mask.png', S) if False else None
Image.fromarray(np.uint8(np.clip(mask, 0, 1) * 255), 'RGBA').save('textures/honkm_region_mask.png')
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
sm2 = 'work/refs/HONKM2.png'; sld = 'work/refs/HONKLEADER.png'
Y_ = lambda px: px @ np.array([.299, .587, .114])
blue = sample_skin(sld, lambda p, h, s: (h > 180) & (h < 225) & (s > .25))
olive = sample_skin(sm2, lambda p, h, s: (h > 42) & (h < 75) & (s > .35))
print('blue', len(blue), (blue.mean(0)), 'olive', len(olive), olive.mean(0))
robe_w = robe; trim_w = trim
tiers = {'honk_a': [ramp(robe_w), ramp(trim_w, olive)], 'honk_b': [ramp(robe_w), ramp(trim_w, olive)], 'honk_c': [ramp(robe_w, blue), ramp(trim_w, olive)]}
json.dump({'variants': list(tiers), 'materials': [{'base': 'HonkM', 'prefix': 'HonkM', 'mask': 'honkm_region_mask.png', 'ramps': tiers}]},
          open('textures/honkm_ramps.json', 'w'), indent=1)
print('REGIONS robe', int(robe.sum()), 'trim', int(trim.sum()), 'yoke', int((yoke & linen).sum()), 'linen', int(linen.sum()))
