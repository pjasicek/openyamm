#!/usr/bin/env python3
"""Face paint pass on a PeasantHOF head set (after head_fix_phof.py and seam_tone.py), on the export GLB's rest positions
(glTF y up, floor 0, +z front). Face lessons: no dark wedges or bruise-grey circles under the eyes, no heavy smoky
eyeshadow, no dark specks at the eye corners, no white specks on the chin/neck.
- Eye surround: per eye an elliptical zone (EYES centres, x/y in m) from the lid ring (opening ellipse OPEN plus a 1.5 mm
  lash ring, untouched) out to RX / RY_UP / RY_DN; texels darker than DARK x the cheek luminance and greyish (saturation
  < SAT) are lifted toward the cheek colour (weight W, feathered 2 mm), keeping 30 % of their own luminance detail.
- Specks: in the same zones, isolated very dark texels (< 0.45 x cheek luminance, connected blobs under 40 texels at 2K)
  outside the lash ring are filled by the lifted surround.
- Chin/neck white specks: skin-shell texels below the mouth (y < MOUTH_Y) brighter than 1.12 x cheek luminance with
  saturation < 0.18 take the cheek colour x their detail (tusks are above MOUTH_Y).
Reads *_prefacepaint.png (written on the first run, or rewritten with RESET=1).
Usage (project folder): face_paint_phof.py <export glb> <head prefix> [--eyes x,y;x,y] [--w 0.75]"""
import argparse, os, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpart import texel_parts
ap = argparse.ArgumentParser()
ap.add_argument('glb'); ap.add_argument('head')
ap.add_argument('--eyes', default='0.0286,1.799;-0.0471,1.7995')
ap.add_argument('--open', default='0.0135,0.006'); ap.add_argument('--rx', type=float, default=0.030)
ap.add_argument('--ry-up', type=float, default=0.0155); ap.add_argument('--ry-dn', type=float, default=0.022)
ap.add_argument('--dark', type=float, default=0.88); ap.add_argument('--sat', type=float, default=0.6)
ap.add_argument('--w', type=float, default=0.6); ap.add_argument('--mouth-y', type=float, default=1.695)
ap.add_argument('--skin', type=int, default=0); ap.add_argument('--head-mat', default='PeasantHOFHead')
ap.add_argument('--dy', type=float, default=0.0); ap.add_argument('--dz', type=float, default=0.0)   # HOF2: its head sits DY/DZ off in the export frame
o = ap.parse_args()
f = Path(f'textures/{o.head}_head_basecolor.png'); bk = f.with_name(f.stem + '_prefacepaint.png')
if not bk.exists() or os.environ.get('RESET') == '1':
    shutil.copyfile(f, bk)
H = np.asarray(Image.open(bk).convert('RGB'), float); N = H.shape[0]
pos, part, _ = texel_parts(o.glb, o.head_mat, N)
P = np.nan_to_num(pos); P[..., 1] -= o.dy; P[..., 2] -= o.dz; skin = part == o.skin; front = skin & (P[..., 2] > -0.03)
mx, mn = H.max(-1), H.min(-1); sat = (mx - mn) / np.maximum(mx, 1); lum = H @ np.array([0.299, 0.587, 0.114])
cheek = front & (P[..., 1] > 1.74) & (P[..., 1] < 1.775) & (np.abs(P[..., 0] + 0.009) > 0.03) & (np.abs(P[..., 0] + 0.009) < 0.06) & \
    (sat > 0.15) & (sat < 0.65)
C = np.median(H[cheek], 0); CL = float(C @ np.array([0.299, 0.587, 0.114]))
ox, oy = [float(v) for v in o.open.split(',')]
out = H.copy(); tot_lift = 0; tot_speck = 0
low = ndimage.gaussian_filter(lum, 6)
for e in o.eyes.split(';'):
    ex, ey = [float(v) for v in e.split(',')]
    dx = (P[..., 0] - ex); dy = (P[..., 1] - ey)
    ry = np.where(dy > 0, o.ry_up, o.ry_dn)
    r_out = np.sqrt((dx / o.rx) ** 2 + (dy / ry) ** 2)
    r_open = np.sqrt((dx / (ox + 0.0015)) ** 2 + (dy / (oy + 0.0015)) ** 2)
    zone = front & (r_out < 1.0) & (r_open > 1.0)
    dark = zone & (lum < o.dark * CL) & (sat < o.sat)
    w = ndimage.gaussian_filter(dark.astype(float), 2.0) * zone
    w *= np.clip((1 - r_out) / 0.15, 0, 1) * np.clip((r_open - 1) / 0.25, 0, 1) * o.w
    det = np.clip(lum / np.maximum(low, 1), 0.7, 1.3) ** 0.3
    out = out * (1 - w[..., None]) + (C[None, None] * det[..., None]) * w[..., None]
    tot_lift += int((w > 0.3).sum())
    sp = zone & (lum < 0.35 * CL)
    lab, n = ndimage.label(sp)
    if n:
        sz = ndimage.sum(sp, lab, range(1, n + 1))
        small = np.isin(lab, 1 + np.nonzero(sz < 40)[0])
        small = ndimage.binary_dilation(small, iterations=2) & zone
        keep = (~small & zone).astype(float)                 # normalised convolution: the surround's own colour
        num = np.stack([ndimage.gaussian_filter(out[..., c] * keep, 4.0) for c in range(3)], -1)
        den = ndimage.gaussian_filter(keep, 4.0)[..., None]
        out[small] = (num / np.maximum(den, 1e-3))[small]; tot_speck += int(small.sum())
lum2 = out @ np.array([0.299, 0.587, 0.114]); mx2, mn2 = out.max(-1), out.min(-1); sat2 = (mx2 - mn2) / np.maximum(mx2, 1)
wh = skin & (P[..., 1] < o.mouth_y) & (lum2 > 1.12 * CL) & (sat2 < 0.3)
wh = ndimage.binary_dilation(wh, iterations=2) & skin & (P[..., 1] < o.mouth_y)
out[wh] = C
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(f)
print('FACEPAINT', o.head, 'cheek', C.round(1).tolist(), 'lifted', tot_lift, 'specks', tot_speck, 'white specks', int(wh.sum()))
