#!/usr/bin/env python3
"""Hairline paint fix (wave-1 lesson: a pale jagged band where the fringe meets the brow). The chestnut fringe ends in
lighter strand tips over skin (8-bit value ~75-90 against the hair's ~60); the tier ramps map luminance, so on row
58's blond those tips came out as a lighter beige line round the hairline. Here, in the composed head set, hair texels
(head region mask R > 0.3) within 8 texels (2K) of the hair border are darkened to at most 1.1 x the hair median luminance
(colour scaled, hue kept). Tier A changes only at the strand tips (a slightly crisper fringe edge).
Usage (project folder): python3 scripts/hairline_fix.py  (reads v2/work/phom1_head_basecolor_composed.png and
v2/textures/phom1_head_region_mask.png, writes v2/textures/phom1_head_basecolor.png); re-run tier_ramps_phom1.py after."""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
base = np.asarray(Image.open('v2/work/phom1_head_basecolor_composed.png').convert('RGB'), float)
N = base.shape[0]
m = np.asarray(Image.open('v2/textures/phom1_head_region_mask.png').getchannel('R').resize((N, N), Image.BILINEAR),
               float) / 255     # the mask's alpha is 0: an RGBA resize would premultiply it to nothing
hair = m > 0.3
lum = base @ np.array([0.2126, 0.7152, 0.0722])
med = float(np.median(lum[m > 0.9]))
# distance from the hair border toward its inside; only borders against covered non-hair texels (skin), not UV gutters
cover = base.sum(-1) > 0
inside = ndi.distance_transform_edt(hair | ~cover)
zone = hair & (inside <= 8)
k = np.where(zone & (lum > 1.1 * med), 1.1 * med / np.maximum(lum, 1e-3), 1.0)   # 1.1: at 1.0 tier A showed a dark rim
k = ndi.gaussian_filter(k, 0.7)
out = np.clip(base * k[..., None], 0, 255)
Image.fromarray(out.round().astype(np.uint8)).save('v2/textures/phom1_head_basecolor.png')
print('HAIRLINE median', round(med, 1), 'texels darkened', int((zone & (lum > med)).sum()))
