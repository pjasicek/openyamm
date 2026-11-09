#!/usr/bin/env python3
"""Breeches top tone (2026-11-02): the 4K paint made the breeches bright gold under and just below the tunic hem (the HD
masters' golden breeches), while their lower legs are darker; the breeches ramp (tier_pm3.py) keeps the paint's brightness
order, so that band stayed bright gold on both tiers (a "gold underskirt" through the side slits and under the hem in
Running). Breeches texels (region mask B) above BAND_Y take a local luminance gain toward the median luminance of the
breeches below it (detail above the 6-texel scale kept), blended in over 4 cm.
Rewrites textures/pm3_tp_basecolor_graded.png (backup work/pm3_tp_basecolor_graded_prebreeches.png on the first run);
then re-run tier_pm3.py (its mask comes from this paint's hues; the breeches mask is geometric).
Usage (project folder): breeches_tone.py work/pm3_body_tex_unlined.glb"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
BAND_Y, RAMP = 0.70, 0.04       # m above the floor (the hem sits at ~0.82-0.85)
glb = sys.argv[1]
src = Path('work/pm3_tp_basecolor_graded_prebreeches.png'); out = Path('textures/pm3_tp_basecolor_graded.png')
if not src.exists():
    shutil.copyfile(out, src)
img = np.asarray(Image.open(src).convert('RGB'), float)
N = img.shape[0]
pos, cov = texel_positions(glb, 'PeasantM3', N)
y = np.nan_to_num(pos[..., 1])
mask = np.asarray(Image.open('textures/pm3_region_mask.png').convert('RGB').resize((N, N), Image.BILINEAR), float)[..., 2] / 255   # RGB: PIL premultiplies an RGBA resize by the mask's zero alpha
br = cov & (mask > 0.5)
lum = img @ [0.299, 0.587, 0.114]
assert br.any(), 'no breeches texels'
ref = np.median(lum[br & (y < BAND_Y - 0.05) & (y > 0.45)])
broad = ndimage.gaussian_filter(np.where(br, lum, 0), 6) / np.maximum(ndimage.gaussian_filter(br.astype(float), 6), 1e-3)
assert np.isfinite(ref)
gain = np.clip(ref / np.maximum(broad, 1), 0.35, 1.0)
w = np.clip((y - BAND_Y) / RAMP, 0, 1) * br
w = ndimage.gaussian_filter(w, 1.0)
res = img * (1 - w[..., None]) + img * gain[..., None] * w[..., None]
Image.fromarray(np.clip(res, 0, 255).astype(np.uint8)).save(out)
print('BREECHES_TONE ref lum %.1f, texels %d, mean gain %.2f' % (ref, int((w > 0.5).sum()), float(gain[w > 0.5].mean())))
