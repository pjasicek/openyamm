#!/usr/bin/env python3
"""Tiers on one shared paint. The paint is the Terror's (skin E, ribs showing), which keeps it untouched (no mask on its material). The cloak and dress are the same on all MM9 skins: no ramps.
Body regions: R the bodice's side and back panels (where the ribs are). The Fright's ramp is nearly flat there, which is how her ribs vanish; the Dread's is the paint's with a warmer, duller colour. G, B and A stay zero: gold, linen, sleeves and hands are the same on every skin.
Hair: a single region, ramps read off BANSHEEA/C/E. Writes textures/banshee_region_mask.png, banshee_hair_mask.png, banshee_ramps.json, banshee_material_classes.png. Run from the project folder."""
import json, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '../claude_shared')
import region_variants as RV
SIZE = 1024
d = np.load('work/uv_v1.npz')
idx, uv, co = d['Body_idx'], d['Body_uv'].copy(), d['Body_co']
part = d['Body_part']
uv[..., 1] = 1 - uv[..., 1]
base = np.asarray(Image.open('textures/banshee_basecolor_graded.png').convert('RGB').resize((SIZE, SIZE), Image.LANCZOS), np.float64) / 255
P = np.zeros((SIZE, SIZE, 3), np.float32); kind = np.zeros((SIZE, SIZE), np.int8)
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
    kind[ys[ok], xs[ok]] = 1 + part[f]
_, (iy, ix) = ndimage.distance_transform_edt(kind == 0, return_indices=True)
kind = kind[iy, ix]; P = P[iy, ix]
x, y, z = P[..., 0], P[..., 1], P[..., 2]
upper = kind == 1
# the front panel and its gold bands stay; side and back panels, down to the belt, up to the shoulder blades
torso = upper & (np.abs(x) < 0.2) & (z > 0.16) & (z < 0.47)
front = (y < -0.135 + 0.0 * x) & (np.abs(x) < 0.112)
R = torso & ~front
R = ndimage.binary_opening(R, iterations=1)
Rw = ndimage.gaussian_filter(R.astype(np.float32), 2.0)
RV.write_mask([Rw, np.zeros_like(Rw), np.zeros_like(Rw), np.zeros_like(Rw)], 'textures/banshee_region_mask.png', SIZE)
RV.write_mask([np.ones((16, 16), np.float32)] + [np.zeros((16, 16), np.float32)] * 3, 'textures/banshee_hair_mask.png', 16)


def ramp(values, stops):
    lo, hi = np.percentile(values, 1), np.percentile(values, 99.5)
    pos = np.array([s[0] for s in stops]); col = RV.srgb_to_linear(np.array([s[1] for s in stops], float) / 255)
    q = np.arange(16) / 15
    return {'range': [round(float(lo), 6), round(float(hi), 6)], 'colors': np.round(np.stack([np.interp(q, pos, col[:, c]) for c in range(3)], 1), 6).tolist()}


vals = RV.srgb_to_linear(base)[R] @ RV.LUMA
FLAT = ramp(vals, [(0, (96, 70, 54)), (0.35, (128, 96, 74)), (0.7, (146, 110, 86)), (1, (170, 134, 108))])
DULL = ramp(vals, [(0, (34, 20, 12)), (0.25, (92, 62, 40)), (0.6, (154, 114, 76)), (1, (216, 182, 138))])
none = {'range': [0.0, 1.0], 'colors': [[0.0, 0.0, 0.0]] * 16}
hair = np.asarray(Image.open('references_swatch/hair.png').convert('RGB').resize((256, 256)), np.float64) / 255
hv = (RV.srgb_to_linear(hair) @ RV.LUMA).ravel()
HA = ramp(hv, [(0, (16, 8, 6)), (0.12, (70, 34, 24)), (0.4, (142, 76, 56)), (0.75, (190, 124, 96)), (1, (232, 186, 156))])
HB = ramp(hv, [(0, (14, 11, 8)), (0.15, (72, 58, 38)), (0.5, (156, 136, 96)), (1, (226, 212, 170))])
HC = ramp(hv, [(0, (10, 7, 4)), (0.15, (84, 64, 38)), (0.5, (190, 168, 122)), (1, (250, 244, 216))])
json.dump({'body': {'banshee_a': [FLAT, none, none, none], 'banshee_b': [DULL, none, none, none]}, 'skirt': {}, 'hair': {'banshee_a': [HA, none, none, none], 'banshee_b': [HB, none, none, none], 'banshee_c': [HC, none, none, none]}}, open('textures/banshee_ramps.json', 'w'))
Image.fromarray(np.where(R, 8, 8).astype(np.uint8)).save('textures/banshee_material_classes.png')
print('REGIONS bodice', round(float(R.mean()), 3))
