#!/usr/bin/env python3
"""The see-through body: texture alpha over the graded colour (one alpha for all tiers; baseColorFactor.a scales it per tier). Torso A_TORSO, hands A_HAND, claws A_CLAW, dress fading from A_ROBE to A_HEM down its length, its hem torn (tears.py, in dress coordinates).
Head A_HEAD. Writes textures/banshee_basecolor_rgba.png, banshee_head_<k>_rgba.png and work/alpha_map.png. Args: head letters. Run from the project folder after the grade."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, 'scripts')
import tears
A_TORSO, A_HAND, A_CLAW, A_ROBE, A_HEM, A_HEAD = 0.72, 0.84, 0.95, 0.66, 0.34, 0.92
SIZE = 2048
T = Path('textures')
d = np.load('work/uv_v1.npz')
idx, uv = d['Body_idx'], d['Body_uv'].copy()
part = d['Body_part']
rs, rt = d['Body_robe_s'], d['Body_robe_t']
uv[..., 1] = 1 - uv[..., 1]
GS, GT = 768, 1536
E_ = tears.tear_field(GS, GT, 11, depth=0.085, periodic=True, holes=10)
A = np.zeros((SIZE, SIZE), np.float32); seen = np.zeros((SIZE, SIZE), bool)
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
    if part[f] == 1:
        w = st[ok]
        b0 = 1 - w[:, 0] - w[:, 1]
        v = idx[f]
        s = b0 * rs[v[0]] + w[:, 0] * rs[v[1]] + w[:, 1] * rs[v[2]]
        # theta wraps: the triangle's corners unwrapped around the first
        th = rt[v].copy()
        th = th + np.where(th - th[0] > 0.5, -1.0, 0.0) + np.where(th - th[0] < -0.5, 1.0, 0.0)
        q = (b0 * th[0] + w[:, 0] * th[1] + w[:, 1] * th[2]) % 1.0
        gs = np.clip((s * (GS - 1)).astype(int), 0, GS - 1); gq = np.clip((q * (GT - 1)).astype(int), 0, GT - 1)
        e = E_[gs, gq]
        cut = np.clip((e + 1.5) / 3.0, 0, 1)
        k = np.clip(s / 0.8, 0, 1); k = k * k * (3 - 2 * k)
        a = (A_ROBE * (1 - k) + A_HEM * k) * cut * (0.7 + 0.3 * np.clip(e / 50, 0, 1))
    else:
        a = np.full(int(ok.sum()), A_CLAW if part[f] == 3 else A_HAND if part[f] == 2 else A_TORSO)
    A[ys[ok], xs[ok]] = a; seen[ys[ok], xs[ok]] = True
_, (iy, ix) = ndimage.distance_transform_edt(~seen, return_indices=True)
A = A[iy, ix]
Image.fromarray((A * 255).astype(np.uint8)).save('work/alpha_map.png')
rgb = Image.open(T / 'banshee_basecolor_graded.png').convert('RGB')
rgb.putalpha(Image.fromarray((A * 255 + 0.5).astype(np.uint8)))
rgb.save(T / 'banshee_basecolor_rgba.png')
for k in sys.argv[1:] or ['a', 'b', 'c']:
    im = Image.open(T / f'banshee_head_{k}_graded.png').convert('RGB')
    im.putalpha(Image.open(T / 'banshee_neck_alpha.png').convert('L'))        # only the Neck primitive is blended; the head is opaque
    im.save(T / f'banshee_head_{k}_rgba.png')
# the mouth bag's patch, on every identity: blood-dark at the lips to black at the throat
import json
rx, ry, rs = json.load(open('scripts/bag_rect.json'))
for k in sys.argv[1:] or ['a', 'b', 'c']:
    im = np.array(Image.open(T / f'banshee_head_{k}_rgba.png'))
    t_ = np.linspace(0, 1, rs)[None, :, None]
    col = (np.array([46, 14, 16.0])[None, None] * (1 - t_) + np.array([5, 2, 3.0])[None, None] * t_)
    im[ry:ry + rs, rx:rx + rs, :3] = col.astype(np.uint8)
    im[ry:ry + rs, rx:rx + rs, 3] = 245
    Image.fromarray(im).save(T / f'banshee_head_{k}_rgba.png')
print('ALPHA mean', float(A.mean()))
