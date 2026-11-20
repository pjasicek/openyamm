#!/usr/bin/env python3
"""Tiers on one shared paint. The paint is Apparition's (B), which keeps it untouched (no mask on its material: a ramp cannot hold its hues). Shadow (A) and Specter (C) recolour by region:
R cloth, G ornament (belt, trims, clasps), B pale linen (ruff, shirt, lace cuffs), A skin (hands). Ramps run from dark to light through colours read off GHOST1 / GHOST3: the flat pale of A
drops the brocade's contrast, which is how the ribs and weave of B vanish on the plain Shadow. Head colour is per identity (head set, see README).
Writes textures/ghost_region_mask.png, ghost_ramps.json, ghost_material_classes.png. Run from the project folder."""
import json, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '../claude_shared')
import region_variants as RV
SIZE = 1024
d = np.load('work/uv_v1.npz')
idx, uv, co = d['Body_idx'], d['Body_uv'].copy(), d['Body_co']
part, hand = d['Body_part'], d['Body_hand']
rs = d['Body_robe_s']
uv[..., 1] = 1 - uv[..., 1]
BELT = 0.046
base = np.asarray(Image.open('textures/ghost_basecolor_graded.png').convert('RGB').resize((SIZE, SIZE), Image.LANCZOS), np.float64) / 255
hsv_max = base.max(2); hsv_min = base.min(2); sat = (hsv_max - hsv_min) / np.maximum(hsv_max, 1e-3)
lum = RV.luminance(base)
import json as _j
_x, _y, _w, _h = _j.load(open('work/collar_uv.json'))['rect']
hollow_ = np.zeros((SIZE, SIZE), np.float32); hollow_[(_y - 6) // 2:(_y + _h + 6) // 2, (_x - 6) // 2:(_x + _w + 6) // 2] = 1
P = np.zeros((SIZE, SIZE, 3), np.float32); kind = np.zeros((SIZE, SIZE), np.int8); S = np.full((SIZE, SIZE), 2.0, np.float32)
for f in range(len(idx)):
    t = uv[f] * SIZE
    lo = np.floor(t.min(0)).astype(int) - 1; hi = np.ceil(t.max(0)).astype(int) + 2
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], SIZE)), np.arange(max(lo[1], 0), min(hi[1], SIZE)))
    if xs.size == 0:
        continue
    mt = np.array([t[1] - t[0], t[2] - t[0]]).T
    if abs(np.linalg.det(mt)) < 1e-9:
        continue
    st = (np.stack([xs + 0.5, ys + 0.5], -1) - t[0]) @ np.linalg.inv(mt).T
    ok = (st[..., 0] >= -0.03) & (st[..., 1] >= -0.03) & (st.sum(-1) <= 1.06)
    if not ok.any():
        continue
    w = st[ok]; b0 = 1 - w[:, 0] - w[:, 1]
    v = idx[f]
    P[ys[ok], xs[ok]] = b0[:, None] * co[v[0]] + w[:, 0:1] * co[v[1]] + w[:, 1:2] * co[v[2]]
    kind[ys[ok], xs[ok]] = 1 + (1 if part[f] == 1 else 0) + (2 if hand[f] else 0)      # 1 upper, 2 robe, 3 hand
    if part[f] == 1:
        S[ys[ok], xs[ok]] = b0 * rs[v[0]] + w[:, 0] * rs[v[1]] + w[:, 1] * rs[v[2]]
_, (iy, ix) = ndimage.distance_transform_edt(kind == 0, return_indices=True)
kind = kind[iy, ix]; S = S[iy, ix]; P = P[iy, ix]
x, y, z = P[..., 0], P[..., 1], P[..., 2]
upper = kind == 1; robe = kind == 2; hnd = kind == 3
belt = robe & (S < BELT)
cuff = upper & (np.abs(x) > 0.46)
pale = upper & (z > 0.1) & (np.abs(x) < 0.12) & (y < -0.02) & (lum > 0.3) & (sat < 0.3)
pale = ndimage.binary_opening(pale, iterations=1) | (upper & (z > 0.41))
trim = upper & (np.abs(x) < 0.16) & (y < -0.02) & (sat > 0.28) & (lum > 0.12) & (lum < 0.5) & ~pale
trim = ndimage.binary_opening(trim, iterations=1)
G = belt | trim
Bm = pale | cuff
Am = hnd
R = ~(G | Bm | Am)
weights = [ndimage.gaussian_filter(m.astype(np.float32), 1.0) for m in (R, G, Bm, Am)]
tot = sum(weights); weights = [w / np.maximum(tot, 1e-3) for w in weights]
hollow = hollow_      # the dark collar hollow keeps its black on every tier
weights = [w * (1 - hollow) for w in weights]
RV.write_mask(weights, 'textures/ghost_region_mask.png', SIZE)


def ramp(mask, stops):
    """stops: [(position 0..1 along the region's luminance range, sRGB)]; 16 colours"""
    values = RV.srgb_to_linear(base)[mask] @ RV.LUMA
    lo, hi = np.percentile(values, 1), np.percentile(values, 99.5)
    pos = np.array([s[0] for s in stops]); col = RV.srgb_to_linear(np.array([s[1] for s in stops], float) / 255)
    q = np.arange(16) / 15
    return {'range': [round(float(lo), 6), round(float(hi), 6)], 'colors': np.round(np.stack([np.interp(q, pos, col[:, c]) for c in range(3)], 1), 6).tolist()}


A = [ramp(R, [(0, (16, 22, 26)), (0.1, (58, 74, 78)), (0.28, (170, 196, 194)), (0.6, (214, 230, 228)), (1, (240, 248, 247))]),
     ramp(G, [(0, (120, 140, 140)), (0.6, (196, 214, 212)), (1, (236, 244, 243))]),
     ramp(Bm, [(0, (170, 190, 190)), (0.5, (222, 234, 233)), (1, (248, 252, 251))]),
     ramp(Am, [(0, (120, 146, 146)), (0.5, (196, 216, 214)), (1, (240, 248, 247))])]
C = [ramp(R, [(0, (6, 10, 16)), (0.12, (16, 28, 40)), (0.35, (34, 58, 80)), (0.7, (100, 130, 152)), (1, (178, 200, 214))]),
     ramp(G, [(0, (34, 44, 54)), (0.5, (116, 132, 140)), (1, (204, 214, 212))]),
     ramp(Bm, [(0, (96, 116, 124)), (0.5, (170, 190, 194)), (1, (226, 236, 238))]),
     ramp(Am, [(0, (70, 100, 112)), (0.5, (150, 182, 190)), (1, (216, 234, 236))])]
json.dump({'ghost_a': A, 'ghost_c': C}, open('textures/ghost_ramps.json', 'w'))
cls = np.full((SIZE, SIZE), 8, np.uint8); cls[Am] = 1
Image.fromarray(cls).save('textures/ghost_material_classes.png')
print('REGIONS', {n: round(float(m.mean()), 3) for n, m in (('cloth', R), ('ornament', G), ('linen', Bm), ('skin', Am))})
