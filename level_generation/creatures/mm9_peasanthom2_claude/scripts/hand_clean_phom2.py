#!/usr/bin/env python3
"""Clean hand paint (user review 2026-11-01, PeasantM7: hands "blotchy and dirty, red/purple mottling, dark grey/black-tipped
nails"; MM9's hands are clean skin). compose_headhand.py graded the MakeHuman hand bake per channel to the spread of the
face paint (stubble, brows and lips included): x2-3 contrast in each channel, so MakeHuman's veins went red/purple and its
pale nails went blue-grey. Here the hand squares of the head set take ONE skin colour (the clean face skin of the head
paint: cheeks and forehead, luminance > 0.45, saturation 0.25-0.6, x GAIN) times the bake's luminance detail only (no hue),
softened (^0.6, within +-15 %) so creases, knuckles and nail edges stay, times the baked AO (no hue: nails come out a little
lighter than the skin, never grey). Gutters are padded like compose_headhand.py. Runs on
v2/textures/phom2_head_basecolor.png (run from v2/) after scripts/hairline_fix.py (which does not touch the hand squares).
Usage (project folder): hand_clean.py [gain 0.95]"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi

GAIN = float(sys.argv[1]) if len(sys.argv) > 1 else 0.95
SQUARES = {"L": [0.8, 0.8, 0.2], "R": [0.8, 0.6, 0.2]}
T = Path('textures/phom2_head_basecolor.png')   # peasanthom1: run from v2/ after scripts/hairline_fix.py
H = Path('work/hands')
img = np.asarray(Image.open(T).convert('RGB')).astype(np.float64)
N = img.shape[0]
# clean face skin of the head paint (lower-left 0.8 square)
k = int(round(N * 0.8))
face = img[N - k:, :k].reshape(-1, 3) / 255
mx, mn = face.max(1), face.min(1)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
lum = face @ np.array([0.299, 0.587, 0.114])
sk = face[(lum > 0.45) & (sat > 0.25) & (sat < 0.6) & (face[:, 0] > face[:, 1]) & (face[:, 1] > face[:, 2])]
ref = np.median(sk, 0) * 255 * GAIN
skin = np.asarray(Image.open(H / 'hand_skin.png').convert('RGB')).astype(np.float64)
mask = np.asarray(Image.open(H / 'hand_mask.png').convert('L')) > 127
ao = np.asarray(Image.open(H / 'hand_ao.png').convert('L').filter(ImageFilter.GaussianBlur(1.6))).astype(np.float64) / 255
L = skin @ np.array([0.299, 0.587, 0.114])
m = mask.astype(np.float64)
m = ndi.binary_erosion(mask, iterations=2).astype(np.float64)
Lb = ndi.gaussian_filter(L * m, 6) / np.maximum(ndi.gaussian_filter(m, 6), 1e-6)
detail = np.clip((L / np.maximum(Lb, 1)) ** 0.6, 0.85, 1.15)
aof = 0.6 + 0.4 * np.clip(ao / max(np.percentile(ao[mask], 90), 1e-3), 0, 1)
aof /= np.median(aof[mask])
col = ref[None, None, :] * (detail * aof)[..., None]
smx, smn = skin.max(2), skin.min(2)
ssat = np.where(smx > 0, (smx - smn) / np.maximum(smx, 1e-6), 0)
nails = mask & (ssat < np.percentile(ssat[mask], 6)) & (L > np.percentile(L[mask], 80))
nails = ndi.binary_opening(nails, iterations=1)
nw = ndi.gaussian_filter(nails.astype(np.float64), 1.0)
# no separate nail tint: the pale/low-saturation test also caught palm texels (pink blobs); the luminance detail alone
# draws the nails a little lighter than the skin
region = np.zeros((N, N), bool)
for u0, v0, side in SQUARES.values():
    x0, x1 = int(u0 * N), int(round((u0 + side) * N)); y0, y1 = N - int(round((v0 + side) * N)), N - int(v0 * N)
    region[y0:y1, x0:x1] = True
hand = mask & region
# the bake's island rims blend into its black background (dark seam lines across the hands, v2.0): colour from texels 2 px
# inside the islands, rims and gutters padded from them
inner = ndi.binary_erosion(mask, iterations=2) & region
out = img.copy()
out[inner] = np.clip(col[inner], 0, 255)
idx = ndi.distance_transform_edt(~inner, return_distances=False, return_indices=True)
grow = ndi.binary_dilation(hand, iterations=24) & region & ~inner
out[grow] = out[idx[0], idx[1]][grow]
Image.fromarray(np.uint8(np.round(out))).save(T)
print('HAND_CLEAN ref', ref.round(1).tolist(), 'hand texels', int(hand.sum()), 'nail texels', int(nails.sum()),
      'old median', np.median(img[hand], 0).round(1).tolist(), 'new median', np.median(out[hand], 0).round(1).tolist())
