#!/usr/bin/env python3
"""One tone across the level head/body seam (face lesson 2026-11-02: no neck seam line; feather both textures to one
tone). Runs after paint_clean.py. The broad colour (mask-normalised Gaussian low-pass, sigma 10 texels at 2K) of both
sets is pulled toward one colour C = the mean of the head set's band just above the cut and the body set's band just
below it (front and sides, |x| < 0.09 m), with weight 1 at the cut fading to 0 at FEATHER above (head) / below (body);
the paint's own detail (img / low-pass) is kept. d1 before: head 209/134/94 above, body 191/124/86 below the cut.
Reads <prefix>_basecolor_graded_preseam.png / <prefix>_head_basecolor_preseam.png (written on the first run, or
rewritten from the current files with RESET=1).
Usage (project folder): seam_tone.py <export glb> <prefix> [--cut 0.909] [--feather 0.035]"""
import argparse, os, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
from headpart import texel_parts
ap = argparse.ArgumentParser()
ap.add_argument('glb'); ap.add_argument('prefix')
ap.add_argument('--cut', type=float, default=0.909); ap.add_argument('--feather', type=float, default=0.035)
ap.add_argument('--body-mat', default='PeasantDF'); ap.add_argument('--head-mat', default='PeasantDFHead')
o = ap.parse_args()


def load(name):
    f = Path(f'textures/{o.prefix}_{name}.png'); bk = f.with_name(f.stem + '_preseam.png')
    if not bk.exists() or os.environ.get('RESET') == '1':
        shutil.copyfile(f, bk)
    return f, np.asarray(Image.open(bk).convert('RGB'), float)


fb, B = load('basecolor_graded'); fh, H = load('head_basecolor')
pb, cb = texel_positions(o.glb, o.body_mat, B.shape[0]); ph, parth, _ = texel_parts(o.glb, o.head_mat, H.shape[0])
ch = parth == 0                      # the head's skin shell only (never the hair/hood part, which hangs below the cut)


def cloth(I):                        # body texels kept out of the pull: blue/green dress cloth and the pale blouse
    mx, mn = I.max(-1), I.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
    r, g, b = I[..., 0], I[..., 1], I[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    return (sat < 0.15) | ((hue > 60) & (hue < 300))

def skinlike(I):                     # warm skin hue, moderate saturation, not dark (d4: the rust collar and the ochre hood are not)
    mx, mn = I.max(-1), I.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
    r, g, b = I[..., 0], I[..., 1], I[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    return (hue > 8) & (hue < 40) & (sat > 0.18) & (sat < 0.62) & (mx > 120)


cb = cb & ~cloth(B) & (np.abs(np.nan_to_num(pb[..., 0])) < 0.17) & ndimage.binary_opening(skinlike(B), iterations=1)
ch = ch & ndimage.binary_opening(skinlike(H), iterations=1)
yb, yh = np.nan_to_num(pb[..., 1]), np.nan_to_num(ph[..., 1])
xb, xh = np.abs(np.nan_to_num(pb[..., 0])), np.abs(np.nan_to_num(ph[..., 0]))
band_b = cb & (yb > o.cut - 0.02) & (yb <= o.cut + 0.001) & (xb < 0.09)
band_h = ch & (yh >= o.cut - 0.001) & (yh < o.cut + 0.02) & (xh < 0.09)
mb, mh = np.median(B[band_b], 0), np.median(H[band_h], 0)
C = 0.5 * (mb + mh)
if os.environ.get('HEAD_ONLY') == '1':   # mm9_peasanthof tier B: a second head set on the shared body; only the head moves
    C = mb


def pull(I, cov, y, sign, s):
    t = np.clip(1 - sign * (y - o.cut) / o.feather, 0, 1) * cov * (np.abs(y - o.cut) < o.feather + 0.01)
    t = ndimage.gaussian_filter(t, 1.0)
    m = (t > 0.01) & cov
    num = ndimage.gaussian_filter(I * m[..., None], (s, s, 0)); den = ndimage.gaussian_filter(m.astype(float), s)
    lp = num / np.maximum(den, 1e-3)[..., None]
    out = I + (C[None, None] - lp) * t[..., None] * (I / np.maximum(lp, 1))
    return np.where(cov[..., None], out, I)


# v3 (face sheet r1: the head band copied from the body read as a lighter collar under the jaw): both sides' broad
# colour meets at C, the mean of the two bands, with weight 1 at the cut easing to 0 at FEATHER on each side
B2 = pull(B, cb, yb, -1, 10 * B.shape[0] / 2048); H2 = pull(H, ch, yh, 1, 10 * H.shape[0] / 2048)
dst = ch & (yh >= o.cut - 0.001) & (yh < o.cut + o.feather)

def pad(I, cov):
    # refill every gutter texel from its nearest covered texel (the compose step padded the gutters before these edits;
    # bilinear sampling at the island edges drew the old colour as a thin line along the cut)
    idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
    return I[idx[0], idx[1]]


H2 = pad(H2, parth >= 0); B2 = pad(B2, texel_positions(o.glb, o.body_mat, B.shape[0])[1])
Image.fromarray(np.uint8(np.clip(np.round(B2), 0, 255))).save(fb)
# normal maps: fade both toward flat at the cut (a strong head normal against a soft body normal shaded as a line)
for name, mat, sign, cov_fn in (('normal_1k', o.body_mat, -1, None), ('head_normal_1k', o.head_mat, 1, None)):
    fn = Path(f'textures/{o.prefix}_{name}.png'); bk = fn.with_name(fn.stem + '_preseam.png')
    if not bk.exists() or os.environ.get('RESET') == '1':
        shutil.copyfile(fn, bk)
    Nm = np.asarray(Image.open(bk).convert('RGB'), float); n = Nm.shape[0]
    if mat == o.head_mat:
        pp, pt, _ = texel_parts(o.glb, mat, n); cv = pt == 0
    else:
        pp, cv = texel_positions(o.glb, mat, n); cv = cv & (np.abs(np.nan_to_num(pp[..., 0])) < 0.17)
    y = np.nan_to_num(pp[..., 1])
    t = ndimage.gaussian_filter(np.clip(1 - sign * (y - o.cut) / 0.01, 0, 1) * cv * (np.abs(y - o.cut) < 0.015), 1.0)
    out = Nm * (1 - t[..., None]) + np.array([128, 128, 255.0]) * t[..., None]
    Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(fn)
Image.fromarray(np.uint8(np.clip(np.round(H2), 0, 255))).save(fh)
print('SEAMTONE', o.prefix, 'body band', mb.round(1), 'head band', mh.round(1), 'C', C.round(1),
      'after: body', np.median(B2[band_b], 0).round(1), 'head', np.median(H2[band_h], 0).round(1), 'head texels', int(dst.sum()))
