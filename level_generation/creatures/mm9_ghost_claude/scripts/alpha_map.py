#!/usr/bin/env python3
"""The see-through: texture alpha over the graded colour (one alpha for all tiers; baseColorFactor.a scales it per tier). Torso A_TORSO, hands A_HAND, robe fading from A_ROBE to A_HEM down its length,
the hem torn by the mask of Meshy's sheets (work/robe_mask.npz) with fine vertical tears. Writes textures/ghost_basecolor_rgba.png, ghost_head_<k>_rgba.png, and work/alpha_map.png.
Run from the project folder after the grade."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
A_TORSO, A_HAND, A_ROBE, A_HEM, A_HEAD = 0.66, 0.78, 0.6, 0.3, 0.9
SIZE = 2048
T = Path('textures')
d = np.load('work/uv_v1.npz')
idx, uv, co = d['Body_idx'], d['Body_uv'].copy(), d['Body_co']
part, hand = d['Body_part'], d['Body_hand']
rs, rt = d['Body_robe_s'], d['Body_robe_t']
uv[..., 1] = 1 - uv[..., 1]
fold = np.where(rt <= 0.5, rt * 2, (1 - rt) * 2)
m = np.load('work/robe_mask.npz')
mask = m['mask']; GS, GT = mask.shape
sdf = ndimage.distance_transform_edt(mask) - ndimage.distance_transform_edt(~mask)
rng = np.random.default_rng(9)
n1 = ndimage.gaussian_filter(rng.normal(size=mask.shape), (26, 2.2)); n1 /= n1.std()
n2 = ndimage.gaussian_filter(rng.normal(size=mask.shape), (9, 1.0)); n2 /= n2.std()
sdfj = sdf + 15 * n1 + 6 * n2
A = np.zeros((SIZE, SIZE), np.float32); seen = np.zeros((SIZE, SIZE), bool); Z = np.zeros((SIZE, SIZE), np.float32)
Z0 = 0.462                     # collar line: above it the neck cone is folded into a dark hollow (collar_head_fix.py); a face with a corner above it (height before the fold) is all hollow
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
    ok = (st[..., 0] >= -0.02) & (st[..., 1] >= -0.02) & (st.sum(-1) <= 1.04)
    if not ok.any():
        continue
    w = st[ok]
    b0 = 1 - w[:, 0] - w[:, 1]
    v = idx[f]
    if part[f] == 1:
        s = b0 * rs[v[0]] + w[:, 0] * rs[v[1]] + w[:, 1] * rs[v[2]]
        q = b0 * fold[v[0]] + w[:, 0] * fold[v[1]] + w[:, 1] * fold[v[2]]
        gs = np.clip((s * (GS - 1)).astype(int), 0, GS - 1); gq = np.clip((q * (GT - 1)).astype(int), 0, GT - 1)
        e = sdfj[gs, gq]
        cut = np.clip((e + 1.5) / 3.0, 0, 1)
        k = np.clip(s / 0.75, 0, 1); k = k * k * (3 - 2 * k)
        a = (A_ROBE * (1 - k) + A_HEM * k) * cut * (0.55 + 0.45 * np.clip(e / 70, 0, 1))
    else:
        a = np.full(int(ok.sum()), A_HAND if hand[f] else A_TORSO)
    A[ys[ok], xs[ok]] = a; seen[ys[ok], xs[ok]] = True
_, (iy, ix) = ndimage.distance_transform_edt(~seen, return_indices=True)
A = A[iy, ix]; Z = Z[iy, ix]
import json
x_, y_, w_, h_ = json.load(open('work/collar_uv.json'))['rect']
kc = np.zeros_like(A); kc[y_ - 4:y_ + h_ + 4, x_ - 4:x_ + w_ + 4] = 1           # the collar bowl's dark patch
Image.fromarray((A * 255).astype(np.uint8)).save('work/alpha_map.png')
rgb = np.asarray(Image.open(T / 'ghost_basecolor_graded.png').convert('RGB'), np.float32)
rgb = rgb * (1 - kc[..., None]) + np.array([7, 9, 10], np.float32) * kc[..., None]
A = A * (1 - kc) + 0.92 * kc
rgb = Image.fromarray(rgb.clip(0, 255).astype(np.uint8))
rgb.putalpha(Image.fromarray((A * 255 + 0.5).astype(np.uint8)))
rgb.save(T / 'ghost_basecolor_rgba.png')
for k in sys.argv[1:] or ['b', 'c']:
    im = Image.open(T / f'ghost_head_{k}_graded.png').convert('RGB')
    im.putalpha(Image.new('L', im.size, int(A_HEAD * 255)))
    im.save(T / f'ghost_head_{k}_rgba.png')
print('ALPHA mean', float(A.mean()))
