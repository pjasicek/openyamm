#!/usr/bin/env python3
"""MM9's PeasantDM3 hides the ears under the hair; ours (flattened by ear_flatten.py) still showed as pale skin in the
gap between cheek and hair curtain. Head-set texels whose rest position lies in the ear zone (lateral 6.4..9.2 cm from
the head axis, z 0.40..0.505, y -0.025..0.07 in Blender rest coordinates) take, where skin-coloured (the ear), the dark hair-shadow
colour (the hair wall's texel) x a faint luminance grain of their own paint, and where hair (the curtain's inner side) their
own paint (unchanged), feathered over 1 cm. The skin of the back and sides of the neck under the
long hair (z 0.28..0.43, behind y 0) gets the same shadow. Reads <prefix>_head_basecolor_preear.png
(made on the first run). Usage (project folder): ear_shade.py <export glb> <prefix>"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
glb, prefix = sys.argv[1:3]
T = Path(f'textures/{prefix}_head_basecolor.png'); B = Path(f'textures/{prefix}_head_basecolor_preear.png')
if not B.exists(): shutil.copy(T, B)
img = np.asarray(Image.open(B).convert('RGB'), np.float64) / 255
N = img.shape[0]
pos, cov = texel_positions(glb, 'PeasantDM3Head', N)
lift = 0.6044                                       # export lifts the rest pose so the soles are at y 0
x, z, y = pos[..., 0], pos[..., 1] - lift, -pos[..., 2]
xc = -0.0101
lat = np.abs(x - xc)
def ramp(v, lo, hi, f=0.01):
    return np.clip((v - lo) / f, 0, 1) * np.clip((hi - v) / f, 0, 1)
w = np.nan_to_num(ramp(lat, 0.050, 0.092) * ramp(z, 0.40, 0.505) * ramp(y, -0.012, 0.07)) * cov
# the back and sides of the neck under the long hair (pink skin showed between hair and collar): z 0.28..0.43, y > 0
wn = np.nan_to_num(ramp(z, 0.28, 0.43, 0.015) * np.clip((y - 0.0) / 0.015, 0, 1)) * cov
w = np.maximum(w, wn)
dark = np.array([0.118, 0.063, 0.043]) * 1.15
lum = img @ [0.2126, 0.7152, 0.0722]
grain = 1 + 0.25 * (lum - np.median(lum[w > 0.5])) if (w > 0.5).any() else 1
# skin (the ear) -> dark hair shadow; hair texels (the curtain's inner side) keep their strands, darkened x 0.6
skinlike = ((img[..., 0] - img[..., 2]) > 0.16) & (lum > 0.28)
shade = np.where(skinlike[..., None], np.clip(dark * np.asarray(grain)[..., None], 0, 1), img)
out = img * (1 - w[..., None]) + shade * w[..., None]
Image.fromarray(np.uint8(np.clip(out, 0, 1) * 255 + 0.5)).save(T)
print('EARSHADE', prefix, 'texels', int((w > 0.01).sum()), 'full', int((w > 0.99).sum()))
