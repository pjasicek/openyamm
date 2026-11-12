#!/usr/bin/env python3
"""Cyan on the trousers (follow-up 5, user 2026-11-12: cyan blob at the crotch, cyan streaks on the dark green trousers).
Cause: the trousers ramp (tier A, palette 748) spans linear luminance 0.009-0.058 and its two top stops are bright cyan; texels
of the trousers region (mask G) above ~0.75 of that range turn cyan. Meshy painted chain mail on the trousers' top charts
(crotch and upper thighs under the hem: the blob and the band under the lifted hem) and bright seam lines/chart rims
(the streaks). Fix: those texels (closed into patches, rims included) are refilled with the surrounding clean trouser
paint (normalized convolution, three scales) plus the fabric's own fine grain, so they stay inside the ramp's dark range.
The ramps, the mask and every other region are unchanged.
Args: <in glb> <out glb> [debug png]"""
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, binary_dilation, binary_closing
from glbtool import Glb, image, replace_image, repack
IN, OUT = sys.argv[1:3]
g = Glb(IN)
LO, HI = 0.009119, 0.057853                    # trousers range (gua_ramps.json, every tier shares it)
POS_BAD, POS_KEEP = 0.68, 0.62
bc = np.asarray(image(g, 'gua_basecolor').convert('RGB')).astype(np.float64) / 255
mk = np.asarray(image(g, 'gua_region_mask').convert('RGB').resize(bc.shape[1::-1], Image.BILINEAR)).astype(np.float64) / 255
w = mk[..., 1]
lin = np.where(bc <= 0.04045, bc / 12.92, ((bc + 0.055) / 1.055) ** 2.4)
pos = (lin @ [0.2126, 0.7152, 0.0722] - LO) / (HI - LO)
tr = w > 0.02
bad0 = tr & (pos > POS_BAD)
dens = gaussian_filter(bad0.astype(float), 3.0)
bad = bad0 | (tr & (dens > 0.18))                                 # mail patches whole (their dark links too)
bad = binary_closing(bad, iterations=2) & tr
bad = binary_dilation(bad, iterations=1) & tr
good = tr & ~bad & (w > 0.5) & (pos < POS_KEEP)
fill = np.zeros_like(bc); wsum = np.zeros(bc.shape[:2])
for s in (2.0, 6.0, 20.0, 60.0):                                  # finest scale that has support wins
    num = np.stack([gaussian_filter(bc[..., c] * good, s) for c in range(3)], -1); den = gaussian_filter(good.astype(float), s)
    take = (wsum < 0.5) & (den > 0.02)
    fill[take] = num[take] / den[take, None]; wsum[take] = 1
# fabric grain: the clean trouser paint's high-pass, tiled from a clean block, at its own amplitude
hp = bc - np.stack([gaussian_filter(bc[..., c], 2.0) for c in range(3)], -1)
ys, xs = np.nonzero(good & (gaussian_filter(good.astype(float), 20) > 0.98))
y0, x0 = ys[len(ys) // 2] - 64, xs[len(xs) // 2] - 64
tile = hp[y0:y0 + 128, x0:x0 + 128]
H, W = bc.shape[:2]
grain = np.tile(tile, (H // 128 + 1, W // 128 + 1, 1))[:H, :W]
new = np.clip(fill + 0.8 * grain, 0, 1)
newlin = np.where(new <= 0.04045, new / 12.92, ((new + 0.055) / 1.055) ** 2.4)
npos = (newlin @ [0.2126, 0.7152, 0.0722] - LO) / (HI - LO)
over = npos > POS_KEEP                                             # grain must not lift a texel back into the cyan stops
new[over] = fill[over]
out = bc.copy(); out[bad] = new[bad]
print('TROUSERS texels fixed', int(bad.sum()), 'of', int(tr.sum()), '; still >0.75 in the trousers:',
      int((tr & (((np.where(out <= 0.04045, out / 12.92, ((out + 0.055) / 1.055) ** 2.4) @ [0.2126, 0.7152, 0.0722] - LO) / (HI - LO)) > 0.75)).sum()))
replace_image(g, 'gua_basecolor', Image.fromarray((out * 255 + 0.5).astype(np.uint8)))
repack(g); g.write(OUT)
if len(sys.argv) > 3:
    vis = (out * 255).astype(np.uint8).copy(); Image.fromarray(vis).save(sys.argv[3])
print('TROUSERS written', OUT)
