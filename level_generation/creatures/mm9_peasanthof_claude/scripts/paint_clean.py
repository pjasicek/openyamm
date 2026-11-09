#!/usr/bin/env python3
"""Paint clean-up of a design's head and body sets where Meshy painted what no reference view showed (d1 review,
2026-11-02): the hair shell's underside / inner rim grey-white, the tucked ears' and the scalp's skin under the hair grey
or dark (a dark spot beside the cheek in three-quarter view), and the neck below the level cut painted as a cream
collar band. Rest positions and loose parts from headpart.py on the export GLB (glTF y up, +z front).
- Hair part (the head set's largest-area part above the face, `--hair-part`): texels with saturation < SAT_MIN, value
  < V_MIN or a hue outside HUE_LO..HUE_HI (the blue-grey inside of the shell) take the broad colour of the nearest good hair texels in 3D (k = 12) times a damped luminance detail.
- Head skin shell (`--skin-part`), only at the sides and back (depth < 0.05 m: never the face front with the eyes, brows
  and lips): texels that are grey (saturation < 0.2) or darker than 0.72 x the good skin median take the nearest good
  skin texels' colour; so do pale texels (saturation < 0.27) on the neck below 0.955 m at any depth (the head
  retexture projected the turnaround's cream neckline onto the bottom of the neck).
- Body set: pale texels (saturation < 0.3, closed) above NECK_LO within |x| < 0.12 m (the base of the neck and the top
  of the chest below the level cut, painted as a cream collar band) take the head set's neck-band skin colour with the
  paint's own fine luminance detail (fade over 1.2 cm above NECK_LO).
Reads/writes textures/<prefix>_head_basecolor.png and <prefix>_basecolor_graded.png (backups *_preclean.png on the first
run; reruns start from them). Usage (project folder): paint_clean.py <export glb> <prefix> [--hair-part 1] [--skin-part 0]
[--sat-min 0.18] [--v-min 70] [--neck-lo 0.865]"""
import argparse, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpart import texel_parts
ap = argparse.ArgumentParser()
ap.add_argument('glb'); ap.add_argument('prefix')
ap.add_argument('--hair-part', type=int, default=1); ap.add_argument('--skin-part', type=int, default=0)
ap.add_argument('--sat-min', type=float, default=0.18); ap.add_argument('--v-min', type=float, default=70)
ap.add_argument('--neck-lo', type=float, default=0.865)
ap.add_argument('--lip-tone', type=float, default=0.0)
ap.add_argument('--hue-lo', type=float, default=10); ap.add_argument('--hue-hi', type=float, default=60)
ap.add_argument('--body-mat', default='PeasantDF'); ap.add_argument('--head-mat', default='PeasantDFHead')
o = ap.parse_args()


def load(name):
    f = Path(f'textures/{o.prefix}_{name}.png'); bk = f.with_name(f.stem + '_preclean.png')
    if not bk.exists() or __import__('os').environ.get('RESET') == '1':
        shutil.copyfile(f, bk)
    return f, np.asarray(Image.open(bk).convert('RGB'), float)


def sv(I):
    mx, mn = I.max(-1), I.min(-1)
    return (mx - mn) / np.maximum(mx, 1), mx


def fill(I, P, good, bad, k=12, detail=0.35):
    """bad texels <- mean colour of the k nearest good texels in 3D, times a damped luminance ratio"""
    if bad.sum() == 0 or good.sum() < k:
        return I, 0
    gi = np.nonzero(good); bi = np.nonzero(bad)
    step = max(1, int(len(gi[0]) / 200000))
    gp = P[gi][::step]; gc = I[gi][::step]
    tree = cKDTree(gp)
    out = I.copy()
    for s in range(0, len(bi[0]), 50000):
        sl = slice(s, s + 50000)
        _, nn = tree.query(P[bi[0][sl], bi[1][sl]], k)
        col = gc[nn].mean(1)
        lum = I[bi[0][sl], bi[1][sl]].mean(-1, keepdims=True); lc = col.mean(-1, keepdims=True)
        ratio = np.clip(lum / np.maximum(lc, 1), 0.6, 1.4) ** detail
        out[bi[0][sl], bi[1][sl]] = col * ratio
    return out, int(bad.sum())


fh, H = load('head_basecolor'); N = H.shape[0]
ph, parth, _ = texel_parts(o.glb, o.head_mat, N)
P = np.nan_to_num(ph); sat, val = sv(H)
hair = parth == o.hair_part
rr, gg, bb = H[..., 0], H[..., 1], H[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (gg - bb), 2 * rr - gg - bb)) % 360
bad_h = hair & ((sat < o.sat_min) | (val < o.v_min) | ~((hue > o.hue_lo) & (hue < o.hue_hi)))
H2, nh = fill(H, P, hair & ~bad_h, bad_h)
skin = parth == o.skin_part
back = skin & (P[..., 2] < 0.05)
med = np.median(val[skin & (P[..., 2] > 0.06) & (sat > 0.2)])
neck = skin & (P[..., 1] < 0.955)
bad_s = (back & ((sat < 0.2) | (val < 0.72 * med))) | (neck & (sat < 0.27))
bad_s = ndimage.binary_dilation(bad_s, iterations=2) & (back | neck)
H3, ns = fill(H2, P, skin & ~bad_s & (sat > 0.2), bad_s)
if o.lip_tone > 0:     # soften lipstick-red lips toward a natural rose (face lesson: no lipstick red)
    rr3, gg3, bb3 = H3[..., 0], H3[..., 1], H3[..., 2]
    hue3 = np.degrees(np.arctan2(np.sqrt(3) * (gg3 - bb3), 2 * rr3 - gg3 - bb3)) % 360
    s3, v3 = sv(H3)
    lips = skin & (P[..., 2] > 0.075) & (np.abs(P[..., 0]) < 0.035) & (P[..., 1] > 0.93) & (P[..., 1] < 1.0) \
        & ((hue3 < 14) | (hue3 > 340)) & (s3 > 0.42)
    cheekm = np.median(H3[skin & (P[..., 2] > 0.06) & (P[..., 1] > 1.0) & (P[..., 1] < 1.04) & (sat > 0.2)], 0)
    rose = cheekm * np.array([0.93, 0.74, 0.74])
    w = ndimage.gaussian_filter(lips.astype(float), 1.2) * o.lip_tone
    lum3 = H3.mean(-1, keepdims=True); det3 = np.clip(lum3 / np.maximum(ndimage.gaussian_filter(lum3, (4, 4, 0)), 1), 0.8, 1.2)
    H3 = H3 * (1 - w[..., None]) + rose * det3 * w[..., None]
    print('LIPS', int(lips.sum()))
neck_ref = np.median(H3[skin & (P[..., 1] > 0.91) & (P[..., 1] < 0.94)], 0)
Image.fromarray(np.uint8(np.clip(np.round(H3), 0, 255))).save(fh)

fb, B = load('basecolor_graded'); NB = B.shape[0]
pb, partb, _ = texel_parts(o.glb, o.body_mat, NB)
Q = np.nan_to_num(pb); cov = partb >= 0
satb, _ = sv(B)
zone = cov & (Q[..., 1] > o.neck_lo) & (np.abs(Q[..., 0]) < 0.12)
pale = zone & (satb < 0.3)
pale = ndimage.binary_closing(pale, iterations=2) & zone
t = ndimage.gaussian_filter(pale.astype(float) * np.clip((Q[..., 1] - o.neck_lo) / 0.012, 0, 1), 1.5) * cov
ax = np.array([0.0, 0.0])
lum = B.mean(-1, keepdims=True); lp = ndimage.gaussian_filter(lum, (8, 8, 0))
det = np.clip(lum / np.maximum(lp, 1), 0.85, 1.15)
B2 = B * (1 - t[..., None]) + neck_ref[None, None] * det * t[..., None]
Image.fromarray(np.uint8(np.clip(np.round(B2), 0, 255))).save(fb)
print('PAINTCLEAN', o.prefix, 'hair texels', nh, 'skin texels', ns, 'neck ref', neck_ref.round(1), 
      'neck texels', int((t > 0.5).sum()))
