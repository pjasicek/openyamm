#!/usr/bin/env python3
"""Upper-lip smudge (PeasantM8, 2026-11-02, head close-ups r2: a dark moustache-like shadow over the character's LEFT upper
lip and mouth corner in profile; the head masters are clean there). In a soft box round the upper lip and mouth corners
(rest z ZLO..ZHI, front of the face, 5..40 mm off the midline) each head-square texel's low-frequency colour (mean of the
texels within R in 3D) is compared with the mirrored point's; where this side is darker, it is multiplied (linear light,
per channel) up to the mirror's mean, so only the darker side moves and the detail stays. Lips (redder than skin) are left.
Reads/writes v2/textures/<prefix>_head_basecolor.png (backup <prefix>_head_basecolor_prelip.png = input of every run).
Usage (project folder): lip_sym.py <prefix> <head texpos npz> [ZLO 0.712] [ZHI 0.745] [R 0.004]"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
pre, tpos = sys.argv[1:3]
ZLO = float(sys.argv[3]) if len(sys.argv) > 3 else 0.712
ZHI = float(sys.argv[4]) if len(sys.argv) > 4 else 0.745
R = float(sys.argv[5]) if len(sys.argv) > 5 else 0.004
CX = -0.017
T = Path('v2/textures'); src = T / f'{pre}_head_basecolor.png'; bak = T / f'{pre}_head_basecolor_prelip.png'
if not bak.exists(): shutil.copy(src, bak)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
H = np.asarray(Image.open(bak).convert('RGB'), np.float32) / 255
N = H.shape[0]; S = int(round(0.8 * N))
pos = np.load(tpos)['pos']
yy, xx = np.mgrid[0:N, 0:N]
m = np.isfinite(pos[..., 0]) & (xx < S) & (yy >= N - S)
ys, xs = np.where(m); P = pos[ys, xs]; C = lin(H[ys, xs])
def sst(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
dx = np.abs(P[:, 0] - CX)
w = sst(P[:, 2], ZLO - 0.004, ZLO) * (1 - sst(P[:, 2], ZHI, ZHI + 0.004)) * sst(dx, 0.002, 0.005) * (1 - sst(dx, 0.035, 0.042)) \
    * (1 - sst(P[:, 1], -0.055, -0.045))
red = (C[:, 0] / np.maximum(C[:, 1], 1e-4))
w *= 1 - sst(red, 2.6, 3.2)                      # lips (much redder than the skin) stay
act = np.where(w > 0)[0]
tree = cKDTree(P)
zone = np.where((P[:, 2] > ZLO - 0.02) & (P[:, 2] < ZHI + 0.02) & (P[:, 1] < -0.03))[0]
zt = cKDTree(P[zone])
def lmean(q):
    out = np.zeros((len(q), 3), np.float32)
    for i, ids in enumerate(zt.query_ball_point(q, R)):
        out[i] = C[zone[ids]].mean(0) if ids else np.nan
    return out
own = lmean(P[act]); Q = P[act].copy(); Q[:, 0] = 2 * CX - Q[:, 0]; mir = lmean(Q)
lo = lambda c: c @ np.array([0.2126, 0.7152, 0.0722])
ok = np.isfinite(mir[:, 0]) & np.isfinite(own[:, 0]) & (lo(mir) > lo(own))
g = np.ones((len(act), 3), np.float32)
g[ok] = np.clip(mir[ok] / np.maximum(own[ok], 1e-4), 1.0, 1.8)
G = 1 + (g - 1) * w[act, None]
out = H.copy(); out[ys[act], xs[act]] = srgb(C[act] * G)
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(src)
side = np.sign(P[act, 0] - CX)
print('LIPSYM', dict(texels=int(len(act)), lifted=int((ok & (g.max(1) > 1.02)).sum()),
                     lifted_plus_x=int((ok & (g.max(1) > 1.02) & (side > 0)).sum()), lifted_minus_x=int((ok & (g.max(1) > 1.02) & (side < 0)).sum()),
                     gain_p90=float(np.percentile(g[ok].max(1), 90)), gain_max=float(g.max())))
