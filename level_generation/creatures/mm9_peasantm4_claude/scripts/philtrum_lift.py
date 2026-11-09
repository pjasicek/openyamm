#!/usr/bin/env python3
"""Upper-lip shade (PeasantM8, 2026-11-02, head close-ups r2/r3): Meshy painted the skin between the nose and the upper lip
darker than the cheeks (luminance 0.45-0.49 against 0.55-0.60, both sides), which reads as a moustache shadow in
profile on a clean-shaven man (MM9's PeasantM8a and the head masters are clean there). Head-square texels in a soft box
(rest z ZLO..ZHI: above the lip line, below the nostrils; within 30 mm of the midline; front of the face), excluding the
lips (much redder than skin), take a low-frequency gain (local mean within R in 3D) toward the cheek luminance TARGET,
1.0..1.3, so the detail stays. Reads/writes v2/textures/<prefix>_head_basecolor.png (backup <prefix>_head_basecolor_prephil.png).
Usage (project folder): philtrum_lift.py <prefix> <head texpos npz> [ZLO 0.721] [ZHI 0.739] [TARGET 0.55] [R 0.004]"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
pre, tpos = sys.argv[1:3]
ZLO, ZHI, TARGET, R = [float(x) for x in sys.argv[3:7]] if len(sys.argv) > 6 else (0.721, 0.739, 0.55, 0.004)
CX = -0.017
T = Path('v2/textures'); src = T / f'{pre}_head_basecolor.png'; bak = T / f'{pre}_head_basecolor_prephil.png'
if not bak.exists(): shutil.copy(src, bak)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
H = np.asarray(Image.open(bak).convert('RGB'), np.float32) / 255
N = H.shape[0]; S = int(round(0.8 * N))
pos = np.load(tpos)['pos']
yy, xx = np.mgrid[0:N, 0:N]
m = np.isfinite(pos[..., 0]) & (xx < S) & (yy >= N - S)
ys, xs = np.where(m); P = pos[ys, xs]; Cs = H[ys, xs]; C = lin(Cs)
def sst(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
dx = np.abs(P[:, 0] - CX)
w = sst(P[:, 2], ZLO - 0.003, ZLO) * (1 - sst(P[:, 2], ZHI, ZHI + 0.003)) * (1 - sst(dx, 0.026, 0.032)) * (1 - sst(P[:, 1], -0.07, -0.06))
red = C[:, 0] / np.maximum(C[:, 1], 1e-4)
w *= 1 - sst(red, 2.6, 3.2)
act = np.where(w > 0)[0]
zone = np.where((P[:, 2] > ZLO - 0.01) & (P[:, 2] < ZHI + 0.01) & (P[:, 1] < -0.05))[0]
zt = cKDTree(P[zone]); lum = Cs @ np.array([0.299, 0.587, 0.114])
loc = np.array([lum[zone[ids]].mean() if ids else np.nan for ids in zt.query_ball_point(P[act], R)])
ok = np.isfinite(loc)
g = np.ones(len(act)); g[ok] = np.clip((TARGET / np.maximum(loc[ok], 1e-3)) ** 2.2, 1.0, 1.3)   # sRGB lum ratio -> linear gain
G = 1 + (g - 1) * w[act]
out = H.copy(); out[ys[act], xs[act]] = srgb(C[act] * G[:, None])
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(src)
print('PHILTRUM', dict(texels=int(len(act)), lum_before_p50=float(np.median(loc[ok])), gain_p50=float(np.median(g[ok])), gain_max=float(g.max())))
