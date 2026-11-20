#!/usr/bin/env python3
"""Torso part against the limbs at the arm cut: per tier and arm, the skin of the torso image eases to the ramped limb colour over the last 8 cm before the cut (gain per channel, low frequency only), so no band shows at the shoulder. Overwrites textures/thrall_torso_{t}_final.png."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '../claude_shared')
import tier_textures as TT
T = Path('textures'); Z = np.load('work/faces.npz'); CO, UV, MAT = Z['co'], Z['uv'], Z['mat']
def raster(sel, S):
    pos = np.zeros((S, S, 3), np.float32); cov = np.zeros((S, S), bool)
    for t in np.nonzero(sel)[0]:
        u = UV[t]; x = u[:, 0] * S; y = (1 - u[:, 1]) * S
        x0, x1 = int(max(np.floor(x.min()) - 1, 0)), int(min(np.ceil(x.max()) + 1, S - 1)); y0, y1 = int(max(np.floor(y.min()) - 1, 0)), int(min(np.ceil(y.max()) + 1, S - 1))
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(d) < 1e-9: continue
        a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
        b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
        g = 1 - a - b; m = (a >= -0.02) & (b >= -0.02) & (g >= -0.02)
        c = CO[t]
        pos[y0:y1 + 1, x0:x1 + 1][m] = (a[..., None] * c[0] + b[..., None] * c[1] + g[..., None] * c[2])[m]; cov[y0:y1 + 1, x0:x1 + 1][m] = True
    return pos, cov
PT, CT = raster(MAT == 1, 2048); PL, CL = raster(MAT == 0, 2048)
R = json.load(open(T / 'thrall_ramps.json'))
base = np.asarray(Image.open(T / 'thrall_limbs_final.png').convert('RGB'), np.float64) / 255
mask = np.stack([np.asarray(ch.resize((2048, 2048), Image.BILINEAR), np.float64) / 255 for ch in Image.open(T / 'thrall_region_mask.png').convert('RGBA').split()], -1)
e = R['materials'][0]
def hsv(a):
    mx, mn = a.max(2), a.min(2); s = (mx - mn) / np.maximum(mx, 1e-6); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, s, mx
for t in 'abc':
    p = T / f'thrall_torso_{t}_final.png'
    q = T / f'thrall_torso_{t}_preseam.png'
    if not q.exists(): q.write_bytes(p.read_bytes())
    im = np.asarray(Image.open(q).convert('RGB'), np.float32) / 255
    h, s, v = hsv(im); skin = (h > 10) & (h < 36) & (s > 0.25) & (v > 0.28)
    L = np.clip(TT.apply(base, mask, e['ramps'][f'thrall_{t}']), 0, 1)
    gain = np.ones((2048, 2048, 3), np.float32)
    for sd in 'LR':
        o, f = Z[sd + 'u'], Z[sd + 'f']; u = (f - o) / np.linalg.norm(f - o)
        st = (PT - o) @ u; sl = (PL - o) @ u
        sx = 1 if sd == 'L' else -1
        side_t = CT & (np.sign(PT[..., 0]) == sx); side_l = CL & (np.sign(PL[..., 0]) == sx)
        ra = side_t & skin & (st > 0.035) & (st < 0.078)
        rb = side_l & (mask[..., 0] > 0.5) & (sl > 0.075) & (sl < 0.11)
        # per azimuth round the arm: the torso paint is lighter on top of the shoulder than underneath
        e1 = np.cross(u, [0, 0, 1.0]); e1 /= np.linalg.norm(e1); e2 = np.cross(u, e1)
        def az(Q): return np.arctan2((Q - o) @ e2, (Q - o) @ e1)
        NB = 24
        bt = ((az(PT) + np.pi) / (2 * np.pi) * NB).astype(int) % NB; bl = ((az(PL) + np.pi) / (2 * np.pi) * NB).astype(int) % NB
        gb = np.ones((NB, 3), np.float32)
        for k in range(NB):
            A_ = ra & (bt == k); B_ = rb & (bl == k)
            if A_.sum() > 100 and B_.sum() > 100:
                gb[k] = np.clip(np.median(L[B_], axis=0) / np.maximum(np.median(im[A_], axis=0), 1e-3), 0.6, 1.5)
        gb = np.stack([ndimage.gaussian_filter1d(gb[:, c], 1.2, mode='wrap') for c in range(3)], -1)
        azt = (az(PT) + np.pi) / (2 * np.pi) * NB - 0.5
        i0 = np.floor(azt).astype(int) % NB; i1 = (i0 + 1) % NB; fr = (azt - np.floor(azt))[..., None]
        g = gb[i0] * (1 - fr) + gb[i1] * fr
        w = np.clip((st + 0.03) / 0.09, 0, 1); w = (w * w * (3 - 2 * w)) * side_t * (st < 0.14)
        w = ndimage.gaussian_filter(w.astype(np.float32), 2.0) * side_t
        gain = gain * (1 + w[..., None] * (g - 1))
        print('SEAM', t, sd, np.round(gb.min(0), 2), np.round(gb.max(0), 2), int(ra.sum()), int(rb.sum()))
    sk = ndimage.gaussian_filter(skin.astype(np.float32), 2.0)[..., None]
    out = im * (1 + sk * (gain - 1))
    Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(p)
print('SEAM done')
