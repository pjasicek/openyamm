#!/usr/bin/env python3
"""Chest skin in the shirt opening matched to the neck (face fix, 2026-11-01; coordinator: "a flat polygonal
skin-coloured panel under the jaw/neck with hard edges on both tiers"). Below the head set's level neck cut the skin
in the shirt's V opening is body-set paint, paler and flatter than the head set's neck, so the jagged cut read as a
panel edge. Body skin texels (warm hue, not the cream shirt, not wool) in the front opening (|x| < 13 cm, rest height
1.30-1.52 m) take a per-channel gain that brings their median to the head set's lowest neck band (1.47-1.50 m) at the
cut, fading to 0 below 1.36 m; luminance detail is kept. Reads the tier A head set (both tiers share the body set and
their neck tones differ by 3-5 levels). Backup textures/pm1_tp_basecolor_graded_prechest.png on the first run.
Usage (project folder): fix_chest.py <export glb>"""
import sys, shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
glb = sys.argv[1]
f = Path('textures/pm1_tp_basecolor_graded.png'); bk = Path('textures/pm1_tp_basecolor_graded_prechest.png')
if not bk.exists():
    shutil.copyfile(f, bk)
body = np.asarray(Image.open(bk).convert('RGB'), float); N = body.shape[0]
pos, cov = texel_positions(glb, 'PeasantM1', N)
x, y, z = (np.nan_to_num(pos[..., i]) for i in range(3))
hd = np.asarray(Image.open('textures/pm1_tp_head_basecolor.png').convert('RGB'), float)
hpos, hcov = texel_positions(glb, 'PeasantM1Head', hd.shape[0])
hy, hz = np.nan_to_num(hpos[..., 1]), np.nan_to_num(hpos[..., 2])
ref = np.median(hd[hcov & (hy > 1.47) & (hy < 1.50) & (hz > 0.02)], 0)
mx, mn = body.max(-1), body.min(-1)
sat = (mx - mn) / np.maximum(mx, 1)
r, g, b = body[..., 0], body[..., 1], body[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
zone = cov & (np.abs(x) < 0.13) & (y > 1.30) & (y < 1.52) & (z > 0.0)
skin = zone & (hue > 5) & (hue < 35) & (sat > 0.22) & (sat < 0.7) & (mx > 120)
src = np.median(body[skin], 0)
gain = ref / src
wy = np.clip((y - 1.36) / (1.47 - 1.36), 0, 1)
w = ndimage.gaussian_filter(skin.astype(float), 1.5) * wy * cov
out = body * (1 + (gain[None, None] - 1) * w[..., None])
near = ndimage.binary_dilation(w > 0.02, iterations=6) & ~cov
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
out[near] = out[iy[near], ix[near]]
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f)
print('FIXCHEST neck ref', ref.round(), 'chest skin median', src.round(), 'gain', gain.round(3), 'texels', int(skin.sum()))
