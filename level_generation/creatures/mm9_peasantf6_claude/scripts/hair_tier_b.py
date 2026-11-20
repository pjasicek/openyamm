#!/usr/bin/env python3
"""Tier B head base: tier A's head paint with the hair recoloured honey-blond -> MM9 PeasantF6B's auburn-chestnut (the face window is then
repainted by the Codex face projection). Hair texels: every texel of the hair shell and the braid, plus the skull texels painted as hair
(blond hue, above the brows, outside the face) - by 3D position from work/headmap.npz. Colour: each hair texel's luminance quantile among
the hair texels mapped onto the luminance-sorted MM9 B hair texels (MM9 region 4 on skin B), times a gain; the strand detail stays.
Args: <A head png> <out png> [gain]   (project folder)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
SRC, DST = sys.argv[1:3]; GAIN = float(sys.argv[3]) if len(sys.argv) > 3 else 1.15
H = np.load('work/headmap.npz'); pos, cov, face = H['pos'], H['cov'], H['face']
D = np.load('work/uv.npz'); comp, tri = D['comp'], D['tri']; names = [str(x) for x in D['names']]
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32)
fc = np.full(cov.shape, -1); fc[cov] = comp[tri[face[cov], 0]]
X, Y, Z = pos[..., 0], pos[..., 1], pos[..., 2]
hsv = np.asarray(Image.open(SRC).convert('HSV'), np.float32) / 255; hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
shell = cov & np.isin(fc, [names.index('hair'), names.index('braid')])
skullhair = cov & (fc == names.index('head')) & (hue > 22) & (hue < 52) & (sat > 0.22) & (val > 0.45) & ((Z > 0.70) | ((np.abs(X) > 0.055) & (Z > 0.645))) & (Y > -0.13)
# the pale blond strands Meshy painted on the skull beside the cheeks under the bob's edge (low saturation, light; skin is sat ~0.6)
pale = cov & (fc == names.index('head')) & (sat < 0.45) & (val > 0.55) & (Z > 0.60) & ((np.abs(X) > 0.045) | (Z > 0.74)) & (Y > -0.12)
# below the bob's edge beside the cheek the pale paint is spill on skin: those texels take the neighbouring skin colour instead
blond = cov & (fc == names.index('head')) & (hue > 22) & (hue < 52) & (sat > 0.22) & (val > 0.45) & (Y > -0.13) & (Y < 0.02)
spill = (pale | blond) & (Z < 0.665) & (Z > 0.58) & (np.abs(X) > 0.045)      # blond paint on the jaw skin under the bob's edge -> skin
pale &= ~spill
# only the front half of the skull (temples, fringe): behind the ears the skull is hidden under the bob, and recoloured skin there showed as
# brown smudges under the bob's edge at the nape
skullhair &= Y < 0.02; pale &= Y < 0.02
skullhair = ni.binary_opening(skullhair | pale, iterations=1)
m = shell | skullhair
w = np.clip(ni.gaussian_filter(m.astype(np.float32), 1.0), 0, 1)
w = w * np.where(shell, 1.0, np.clip((Z - 0.645) / 0.04, 0, 1) + (Z > 0.70))      # skull hair fades out downward (no hard edge at the temples)
w = np.clip(w, 0, 1); w[shell] = 1
lum = im @ np.array([0.2126, 0.7152, 0.0722])
# MM9 B hair texels
ML = np.load('work/mm9_regions.npy'); SK = np.asarray(Image.open('source/mm9/skins/pf6b.png').convert('RGB'), np.float32)
hb = np.asarray(Image.open('source/mm9/skins/pf6b.png').convert('HSV'), np.float32) / 255
tgt = SK[(ML == 4) & (hb[..., 1] > 0.35) & (hb[..., 0] * 360 < 45)]
tl = tgt @ np.array([0.2126, 0.7152, 0.0722]); ts = tgt[np.argsort(tl)]
lv = lum[m]; order = np.argsort(np.argsort(lv)); q = order / max(len(lv) - 1, 1)
col = ts[np.clip((q * (len(ts) - 1)).astype(int), 0, len(ts) - 1)]
# keep the paint's own fine strand contrast: the quantile colour sets the broad tone, the local luminance ratio the strands
lb = ni.gaussian_filter(lum, 3)[m] + 1; ratio = np.clip(lum[m] / lb, 0.7, 1.35)
broad = ni.gaussian_filter(np.zeros_like(lum), 1)
out = im.copy(); new = np.clip(col * GAIN, 0, 255)
nb = new.mean(1, keepdims=True); new = np.clip(new * (ratio[:, None] ** 0.5), 0, 255)
full = im.copy(); full[m] = new
out = im * (1 - w[..., None]) + full * w[..., None]
skinref = cov & (fc == names.index('head')) & ~m & ~pale & ~spill & (sat > 0.45) & (Z > 0.56) & (Z < 0.68) & (np.abs(X) > 0.035)
if spill.any() and skinref.any():
    from scipy.spatial import cKDTree
    d_, n_ = cKDTree(pos[skinref]).query(pos[spill], k=16); sw = np.clip(ni.gaussian_filter(spill.astype(np.float32), 1.5), 0, 1)
    sc = np.zeros_like(out); sc[spill] = out[skinref][n_].mean(1); sc = np.where(spill[..., None], sc, out)
    out = out * (1 - sw[..., None]) + sc * sw[..., None]
print('spill texels', int(spill.sum()))
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); out = out[idx[0], idx[1]]
Image.fromarray(np.clip(out + .5, 0, 255).astype('u1')).save(DST)
print('HAIR_B', int(shell.sum()), 'shell', int(skullhair.sum()), 'skull texels; MM9 B hair median', np.median(tgt, 0).round(0).tolist(), 'ours median', np.median(new, 0).round(0).tolist())
