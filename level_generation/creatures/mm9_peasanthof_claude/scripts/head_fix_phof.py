#!/usr/bin/env python3
"""Paint clean-up of a PeasantHOF head + hands set and the neck of the body set (after compose_headhand.py), on the export
GLB's rest positions (glTF: y up, floor 0, +z front; head parts from headpart.py, largest first):
- skin shell (part SKIN): grey or dark texels at the sides/back (z < BACK_Z) and pale/grey texels on the neck below NECK_Y
  take the nearest good skin texels' colour (k-nn in 3D) times a damped luminance detail;
- ears (EARS parts, the procedural pointed ears): the cheek skin colour times their own luminance detail (Meshy painted
  them a flat pale salmon, lighter and pinker than the face);
- hair (HAIR parts: shell and braids): grey, very dark or off-hue texels take the nearest good hair colour;
- body set: pale texels (saturation < 0.3) on the front of the neck/chest just below the cut (y > BODY_NECK_LO, |x| < 0.12,
  z > -0.06) take the neck skin colour (the retexture painted a cream collar band there).
Reads *_preclean.png backups (written on the first run or with RESET=1).
Usage (project folder): head_fix_phof.py <export glb> <head prefix> <body prefix> [--skin 0] [--hair 3,4,5,6,7] [--ears 8,9]"""
import argparse, os, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpart import texel_parts
ap = argparse.ArgumentParser()
ap.add_argument('glb'); ap.add_argument('head'); ap.add_argument('body')
ap.add_argument('--skin', type=int, default=0); ap.add_argument('--hair', default='3,4,5,6,7'); ap.add_argument('--ears', default='8,9')
ap.add_argument('--back-z', type=float, default=0.0); ap.add_argument('--neck-y', type=float, default=1.685)
ap.add_argument('--body-neck-lo', type=float, default=1.56); ap.add_argument('--neck-top', type=float, default=1.70); ap.add_argument('--ear-detail', type=float, default=0.6); ap.add_argument('--ear-gain', type=float, default=0.72)
ap.add_argument('--hue-lo', type=float, default=4); ap.add_argument('--hue-hi', type=float, default=48)
ap.add_argument('--body-mat', default='PeasantHOF'); ap.add_argument('--head-mat', default='PeasantHOFHead')
ap.add_argument('--chin-half', type=float, default=0.0)   # >0: the neck evening spares only the chin front within this |x|
ap.add_argument('--dy', type=float, default=0.0); ap.add_argument('--dz', type=float, default=0.0)   # HOF2: its head sits DY/DZ off in the export frame
o = ap.parse_args()


def load(name):
    f = Path(f'textures/{name}.png'); bk = f.with_name(f.stem + '_preclean.png')
    if not bk.exists() or os.environ.get('RESET') == '1':
        shutil.copyfile(f, bk)
    return f, np.asarray(Image.open(bk).convert('RGB'), float)


def hsv(I):
    mx, mn = I.max(-1), I.min(-1)
    r, g, b = I[..., 0], I[..., 1], I[..., 2]
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, (mx - mn) / np.maximum(mx, 1), mx


def fill(I, P, good, bad, k=12, detail=0.35):
    if bad.sum() == 0 or good.sum() < k:
        return I, 0
    gi = np.nonzero(good); bi = np.nonzero(bad)
    step = max(1, int(len(gi[0]) / 200000))
    tree = cKDTree(P[gi][::step]); gc = I[gi][::step]
    out = I.copy()
    for s in range(0, len(bi[0]), 50000):
        sl = slice(s, s + 50000)
        _, nn = tree.query(P[bi[0][sl], bi[1][sl]], k)
        col = gc[nn].mean(1)
        lum = I[bi[0][sl], bi[1][sl]].mean(-1, keepdims=True); lc = col.mean(-1, keepdims=True)
        out[bi[0][sl], bi[1][sl]] = col * np.clip(lum / np.maximum(lc, 1), 0.6, 1.4) ** detail
    return out, int(bad.sum())


fh, H = load(f'{o.head}_head_basecolor'); N = H.shape[0]
ph, part, _ = texel_parts(o.glb, o.head_mat, N)
P = np.nan_to_num(ph); P[..., 1] -= o.dy; P[..., 2] -= o.dz; hue, sat, val = hsv(H)
skin = part == o.skin
hairp = np.isin(part, [int(x) for x in o.hair.split(',') if x])
earp = np.isin(part, [int(x) for x in o.ears.split(',') if x])
cheek = skin & (P[..., 2] > 0.0) & (P[..., 1] > 1.70) & (P[..., 1] < 1.78) & (np.abs(P[..., 0]) > 0.025) & \
    (np.abs(P[..., 0]) < 0.07) & (sat > 0.18) & (sat < 0.55) & (val > 140)
C = np.median(H[cheek], 0)
med = np.median(val[skin & (P[..., 2] > 0.0) & (sat > 0.18) & (val > 120)])
# hair first (its good texels are the reference for its bad ones)
bad_h = hairp & ((sat < 0.25) | (val < 45) | ~((hue > o.hue_lo) & (hue < o.hue_hi)))
H2, nh = fill(H, P, hairp & ~bad_h, bad_h)
# skin shell: grey/dark sides and back, pale neck band
skin_like = (hue < 40) | (hue > 345)
back = skin & ((P[..., 2] < o.back_z) | (np.abs(P[..., 0]) > 0.072))   # sides, temples and back (not the face front: eye whites, tusks)
neck = skin & (P[..., 1] < o.neck_y)
hairish = (sat > 0.5) & (val < 200)                     # auburn hair painted on the shell (fringe, sideburns): keep
bad_s = ((back | neck) & ~hairish & ((sat < 0.2) | ((val < 0.72 * med) & skin_like))) | (neck & ~hairish & (sat < 0.27))
bad_s = ndimage.binary_dilation(bad_s, iterations=2) & (back | neck)
good_s = skin & ~bad_s & (sat > 0.18) & (val > 0.8 * med) & skin_like & (P[..., 1] < 1.80) & (P[..., 1] > 1.62)
H3, ns = fill(H2, P, good_s, bad_s)
# pale grey-beige panels on the skin shell (coordinator review r2: light rectangles at the temples and along the hairline
# that framed the warmed face): any shell texel paler and greyer than the skin, outside the eyes and the mouth, takes the
# nearest good skin colour (eye whites and tusks are kept by the two exclusion boxes)
_, sat3, val3 = hsv(H3)
eyes = (np.abs(P[..., 1] - 1.80) < 0.014) & (np.abs(np.abs(P[..., 0] + 0.009) - 0.037) < 0.024) & (P[..., 2] > -0.01)
mouth = (np.abs(P[..., 0] + 0.009) < 0.04) & (P[..., 1] > 1.695) & (P[..., 1] < 1.745) & (P[..., 2] > -0.01)
pale = skin & ~hairp & (sat3 < 0.22) & (val3 > 0.8 * med) & ~eyes & ~mouth & ~((sat3 > 0.5) & (val3 < 200))
pale = ndimage.binary_dilation(pale, iterations=1) & skin & ~eyes & ~mouth
H3, npale = fill(H3, P, good_s, pale, detail=0.5)
print('PALEFILL texels', npale)
# ears: cheek colour x own luminance detail
lum = H3.mean(-1)
ne = int(earp.sum())
if ne:
    el = lum[earp]; ratio = np.clip(lum / max(np.median(el), 1), 0.55, 1.35) ** o.ear_detail
    H3[earp] = (C[None] * o.ear_gain * ratio[earp][:, None])   # thin ears face the light: a little darker than the cheek
neck_ref = np.median(H3[skin & (P[..., 1] > o.neck_y - 0.02) & (P[..., 1] < o.neck_y + 0.01) & (P[..., 2] > -0.02) &
                        (sat > 0.18)], 0)
# neck evening (face sheet r1: lighter angular patches on the neck sides below the jaw, UV islands painted lighter): head
# skin below NECK_TOP (not the chin's front) takes the neck colour as its broad colour, its own detail kept
if o.neck_top > 0:
    chin = (P[..., 2] > 0.0) & (P[..., 1] > o.neck_top - 0.045)
    if o.chin_half > 0:     # r2 face sheet: pale triangles under the jaw corners (front, beside the chin) were spared too
        chin &= np.abs(P[..., 0] + 0.009) < o.chin_half
    zone = skin & (P[..., 1] < o.neck_top) & ~chin & ~hairish
    lum3 = H3.mean(-1)
    low = np.stack([ndimage.gaussian_filter(H3[..., c] * zone, 10) for c in range(3)], -1) / \
        np.maximum(ndimage.gaussian_filter(zone.astype(float), 10), 1e-3)[..., None]
    w = ndimage.gaussian_filter(zone.astype(float), 2.0) * skin
    H3 = H3 + (neck_ref[None, None] - low) * w[..., None] * (H3 / np.maximum(low, 1))
    print('NECKEVEN texels', int(zone.sum()))
Image.fromarray(np.uint8(np.clip(np.round(H3), 0, 255))).save(fh)

fb, B = load(f'{o.body}_basecolor_graded'); NB = B.shape[0]
pb, partb, _ = texel_parts(o.glb, o.body_mat, NB)
Q = np.nan_to_num(pb); Q[..., 1] -= o.dy; Q[..., 2] -= o.dz; cov = partb >= 0
_, satb, _ = hsv(B)
zone = cov & (Q[..., 1] > o.body_neck_lo) & (np.abs(Q[..., 0]) < 0.12) & (Q[..., 2] > -0.06)
pale = ndimage.binary_closing(zone & (satb < 0.3), iterations=2) & zone
t = ndimage.gaussian_filter(pale.astype(float) * np.clip((Q[..., 1] - o.body_neck_lo) / 0.012, 0, 1), 1.5) * cov
lb = B.mean(-1, keepdims=True); det = np.clip(lb / np.maximum(ndimage.gaussian_filter(lb, (8, 8, 0)), 1), 0.85, 1.15)
B2 = B * (1 - t[..., None]) + neck_ref[None, None] * det * t[..., None]
Image.fromarray(np.uint8(np.clip(np.round(B2), 0, 255))).save(fb)
print('HEADFIX', o.head, 'cheek', C.round(1).tolist(), 'hair texels', nh, 'skin texels', ns, 'ear texels', ne,
      'neck ref', neck_ref.round(1).tolist(), 'body neck texels', int((t > 0.5).sum()))
