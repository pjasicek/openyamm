#!/usr/bin/env python3
"""Warmer, ruddier skin for one tier (coordinator review 2026-11-02: tier A read pale and grey-pink; MM9's half-orc women have
warm ruddy skin). Skin texels of the head set (skin shell, ears, hands: warm hue 0-40 deg, saturation 0.12-0.6, not hair)
and of the body set (the tier region mask's skin channel B > 0.3) take a per-channel gain GAIN (sRGB); on the face a soft
cheek flush (Gaussian 2.5 cm round each cheek, FLUSH strength toward a rose-brown). Reads *_prewarm.png backups.
Usage (project folder): skin_warm.py <export glb> <head prefix> <body prefix> <region mask png> [--gain 1.0,0.93,0.84] [--flush 0.22]"""
import argparse, os, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpart import texel_parts
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('head'); ap.add_argument('body'); ap.add_argument('mask')
ap.add_argument('--gain', default='1.0,0.93,0.84'); ap.add_argument('--flush', type=float, default=0.22)
ap.add_argument('--cheeks', default='-0.058,1.765;0.040,1.765')
ap.add_argument('--body-auto', action='store_true', help='head untouched; the body skin takes the gain that maps its median onto the head neck band median')
o = ap.parse_args()
G = np.array([float(x) for x in o.gain.split(',')])
def load(name):
    f = Path(f'textures/{name}.png'); bk = f.with_name(f.stem + '_prewarm.png')
    if not bk.exists() or os.environ.get('RESET') == '1': shutil.copyfile(f, bk)
    return f, np.asarray(Image.open(bk).convert('RGB'), float)
fh, H = load(f'{o.head}_head_basecolor'); N = H.shape[0]
pos, part, _ = texel_parts(o.glb, 'PeasantHOFHead', N); P = np.nan_to_num(pos)
r, g, b = H[..., 0], H[..., 1], H[..., 2]
mx, mn = H.max(-1), H.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
skin = (part >= 0) & ((hue < 40) | (hue > 350)) & (sat > 0.12) & (sat < 0.6) & ~((sat > 0.45) & (mx < 200)) & (mx > 90) & ~((mx > 200) & (sat < 0.36))   # not the ivory tusks
w = ndimage.gaussian_filter(skin.astype(float), 1.0) * (part >= 0) * (0.0 if o.body_auto else 1.0)
out = H * (1 - w[..., None]) + np.clip(H * G, 0, 255) * w[..., None]
rose = np.array([200.0, 112.0, 92.0])
fl = np.zeros(H.shape[:2])
for q in o.cheeks.split(';'):
    cx, cy = [float(t) for t in q.split(',')]
    d2 = (P[..., 0] - cx) ** 2 + (P[..., 1] - cy) ** 2
    fl = np.maximum(fl, np.exp(-d2 / (2 * 0.018 ** 2)) * (P[..., 2] > -0.01) * (part == 0))
fl *= o.flush * w * (0.0 if o.body_auto else 1.0)
lum = out.mean(-1, keepdims=True); det = lum / np.maximum(ndimage.gaussian_filter(lum, (4, 4, 0)), 1)
out = out * (1 - fl[..., None]) + rose * det * fl[..., None]
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(fh)
fb, B = load(f'{o.body}_basecolor_graded')
M = np.asarray(Image.open(o.mask).convert('RGBA').split()[2].resize((B.shape[1], B.shape[0]), Image.BILINEAR), float) / 255   # one channel: RGBA resizes premultiplied
if o.body_auto:
    nb = skin & (P[..., 1] > 1.64) & (P[..., 1] < 1.70) & (P[..., 2] > -0.03)
    GB = np.median(H[nb], 0) / np.maximum(np.median(B[M > 0.7], 0), 1)
    print('BODYAUTO gain', GB.round(3).tolist())
else:
    GB = G
B2 = B * (1 - M[..., None]) + np.clip(B * GB, 0, 255) * M[..., None]
Image.fromarray(np.uint8(np.clip(np.round(B2), 0, 255))).save(fb)
print('SKINWARM', o.head, 'head skin texels', int(skin.sum()), 'body skin', int((M > 0.5).sum()), 'cheek before',
      np.median(H[(fl > 0.1 * o.flush)], 0).round().tolist() if (fl > 0.1 * o.flush).any() else None,
      'after', np.median(out[(fl > 0.1 * o.flush)], 0).round().tolist() if (fl > 0.1 * o.flush).any() else None)
