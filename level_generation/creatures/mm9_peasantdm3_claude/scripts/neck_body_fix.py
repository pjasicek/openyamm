#!/usr/bin/env python3
"""Body paint: skin-coloured texels of the body set around the neck opening (rest z > 0.30, behind y -0.03: the collar's
inner rim and the neck stub of the body mesh, which the body retexture painted as neck skin from the DM1-silhouette
masters) showed as pink patches under the long hair (review/t8_faces.png). They take the dark hair-shadow colour with a
faint grain of their own luminance, feathered. Reads textures/<prefix>_basecolor_graded_preneck.png (made on the first run).
Usage (project folder): neck_body_fix.py <export glb> <prefix>"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
glb, prefix = sys.argv[1:3]
T = Path(f'textures/{prefix}_basecolor_graded.png'); B = Path(f'textures/{prefix}_basecolor_graded_preneck.png')
if not B.exists(): shutil.copy(T, B)
img = np.asarray(Image.open(B).convert('RGB'), np.float64) / 255
N = img.shape[0]
pos, cov = texel_positions(glb, 'PeasantDM3', N)
lift = 0.6044
z, y = pos[..., 1] - lift, -pos[..., 2]
lum = img @ [0.2126, 0.7152, 0.0722]
r_ = np.maximum(img[..., 0], 1e-3); gr, br = img[..., 1] / r_, img[..., 2] / r_
# skin hue only (the ochre braid, gold brooch and brown beads have b/r < 0.4)
skin = (lum > 0.30) & (gr > 0.55) & (gr < 0.85) & (br > 0.42) & (br < 0.78) & ((img[..., 0] - img[..., 2]) > 0.15)
zone = np.nan_to_num((z > 0.30) & (y > -0.03)).astype(bool) & cov
m = ndimage.binary_dilation(skin & zone, iterations=2) & zone
w = ndimage.gaussian_filter(m.astype(float), 1.0) * zone
dark = np.array([0.118, 0.063, 0.043]) * 1.15
grain = 1 + 0.25 * (lum - np.median(lum[m])) if m.any() else np.ones_like(lum)
out = img * (1 - w[..., None]) + np.clip(dark * grain[..., None], 0, 1) * w[..., None]
Image.fromarray(np.uint8(np.clip(out, 0, 1) * 255 + 0.5)).save(T)
print('NECKBODY', prefix, 'texels', int(m.sum()))
