#!/usr/bin/env python3
"""Per-tier head colour (face, hair, circlet, hood): the hood texels of each tier's own head paint (Morgan blue, Verdandi olive damask, found
by hue) are quantile-mapped onto MM9's mantle texels of that tier (the same target as the body's mantle ramp, so hood and mantle meet at the
cut without a colour step); face, hair and circlet keep the paint. Luminance detail (folds, Verdandi's damask) stays.
Args: <tier y|m> <in png> <out png> [mask preview png]  (project folder)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
T, SRC, DST = sys.argv[1:4]; PREV = sys.argv[4] if len(sys.argv) > 4 else None
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255; S = im.shape[0]
def lin(a): return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
def unlin(a): return np.where(a <= 0.0031308, a * 12.92, 1.055 * np.maximum(a, 0) ** (1 / 2.4) - 0.055)
LUMA = np.array([0.2126, 0.7152, 0.0722])
hsv = np.asarray(Image.fromarray((im * 255).astype('u1')).convert('HSV'), np.float32) / 255; h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
if T == 'y':
    hood = (h > 195) & (h < 260) & (s > 0.25)
else:
    goldm = (h > 28) & (h < 56) & (s > 0.55) & (v > 0.55)
    hood = (((h > 45) & (h < 110) & (s > 0.25)) | ((h > 35) & (h <= 45) & (s > 0.3) & (v < 0.45))) & (v > 0.06) & ~goldm
hood = ni.binary_opening(hood, iterations=1); hood = ni.binary_closing(hood, iterations=2)
lab, n = ni.label(hood); sz = ni.sum(hood, lab, range(1, n + 1)); hood = np.isin(lab, 1 + np.where(sz >= 60)[0])
# MM9 mantle texels of this tier (256 skin): the plain back strip and the hood drape
sk = np.asarray(Image.open(f"source/mm9/wyrd_{'young' if T == 'y' else 'mature'}/skins/wyrd_{'young' if T == 'y' else 'mature'}.png").convert('RGB'), np.float32) / 255
kh = np.asarray(Image.fromarray((sk * 255).astype('u1')).convert('HSV'), np.float32) / 255
yy, xx = np.mgrid[0:256, 0:256]; zone = ((xx >= 200) & (xx < 254)) | ((xx > 40) & (xx < 125) & (yy < 140))
if T == 'y': tm = zone & (kh[..., 0] * 360 > 200) & (kh[..., 0] * 360 < 260) & (kh[..., 1] > 0.3)
else: tm = zone & (kh[..., 0] * 360 > 40) & (kh[..., 0] * 360 < 100) & (kh[..., 1] > 0.3)
tgt = lin(sk[tm]); tl = tgt @ LUMA; tgt = tgt[np.argsort(tl)]
L = lin(im); l = L @ LUMA; lv = np.sort(l[hood])
q = np.searchsorted(lv, l) / max(len(lv), 1)            # each texel's quantile among the hood texels
col = np.zeros_like(L); n_ = len(tgt)
# 64 quantile bins, each the mean of its band of the target (no texel noise from the 256 skin)
bins = np.clip((q * 64).astype(int), 0, 63); means = np.array([tgt[int(b / 64 * n_):max(int(b / 64 * n_) + 1, int((b + 1) / 64 * n_))].mean(0) for b in range(64)])
col = means[bins]
w = np.clip(ni.gaussian_filter(hood.astype(np.float32), 1.0), 0, 1)[..., None] * hood[..., None] + 0 * col
w = np.clip(ni.gaussian_filter(hood.astype(np.float32), 0.8), 0, 1)[..., None]
out = unlin(L * (1 - w) + col * w)
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(DST)
print('HEADTIER', T, 'hood texels', int(hood.sum()), 'of', S * S, 'MM9 targets', int(tm.sum()), 'median', np.round(unlin(np.median(tgt, 0)) * 255).tolist())
if PREV:
    pv = (im * 255).astype('u1').copy(); pv[hood] = (pv[hood] * 0.3 + np.array([255, 0, 255]) * 0.7).astype('u1'); Image.fromarray(pv).save(PREV)
# ---- Morgan (y): Meshy painted the hair under the hood and at the temples dark brown (a brunette under the hood); MM9's Morgan is blonde
# throughout. Dark brown hair texels (hue 8-45, sat > 0.3, value < 0.42) off the face front take the paint's own blonde, shaded by their
# luminance (texel_pos.py <size> 1 -> work/texel_pos_head.npy)
if T == 'y':
    import os
    P3 = np.load('work/texel_pos_head.npy'); okp = ~np.isnan(P3[..., 0]); P3 = np.nan_to_num(P3)
    o8 = np.asarray(Image.open(DST).convert('RGB'), np.float32) / 255
    hv = np.asarray(Image.fromarray((o8 * 255).astype('u1')).convert('HSV'), np.float32) / 255; hh, ss_, vv = hv[..., 0] * 360, hv[..., 1], hv[..., 2]
    face = (P3[..., 1] < -0.08) & (P3[..., 2] < 0.715)
    dark = okp & ((hh < 45) | (hh > 345)) & (ss_ > 0.25) & (vv < 0.50) & ~face & (P3[..., 2] > 0.60)
    blond = okp & (hh > 32) & (hh < 52) & (ss_ > 0.25) & (ss_ < 0.7) & (vv > 0.6)
    Lb = lin(o8); cb = np.median(Lb[blond], 0); lb = cb @ LUMA; l8 = Lb @ LUMA
    newc = cb[None, None, :] * np.clip(l8 / lb * 3.0, 0.40, 0.95)[..., None]
    wd = np.clip(ni.gaussian_filter(dark.astype(np.float32), 0.8), 0, 1)[..., None] * okp[..., None]
    o8 = unlin(Lb * (1 - wd) + newc * wd)
    Image.fromarray((np.clip(o8, 0, 1) * 255 + .5).astype('u1')).save(DST); print('HAIR blonde under the hood', int(dark.sum()), 'texels')
