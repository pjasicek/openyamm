#!/usr/bin/env python3
"""Body paint fix (2026-11-01): Meshy painted the front laces a second time on the BACK of the tunic (two cream cords
hanging from the nape, seen in the first viewer shots; the back master has none). Their texels (rest-pose position
on the back: y > 0, z 0.30-0.66, |x| < 0.12, pale and unsaturated) plus a 3-texel rim are refilled from the tunic
around them (also the cream paint of the left armpit fin that geo_fix.py laid down: x 0.12-0.26, z 0.36-0.54): a normalised Gaussian fill of the surrounding colour, plus the surrounding weave's own fine detail
copied from 24 texels away along the chart. Writes textures/pm1d_basecolor.png in place (the untouched Meshy compose
is kept as textures/pm1d_basecolor_meshy.png); grade afterwards as before.
Usage (project folder): ../claude_shared/gltf_venv/bin/python scripts/tex_fix.py"""
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texel_xyz import texel_xyz  # noqa: E402

N = 2048
src = Path('textures/pm1d_basecolor_meshy.png')
if not src.exists():
    shutil.copy('textures/pm1d_basecolor.png', src)
img = np.asarray(Image.open(src).convert('RGB'), float) / 255
d = np.load('v2/work/uv_UVMap.npz')
X, cov, _ = texel_xyz('v2/work/uv_UVMap.npz', N, (d['head'] == 0) & (d['hand'] == 0))
mx = img.max(-1); s = (mx - img.min(-1)) / (mx + 1e-9)
x, y, z = X[..., 0], X[..., 1], X[..., 2]
lace = cov & (y > 0.0) & (z > 0.30) & (z < 0.66) & (np.abs(x) < 0.12) & (s < 0.55) & (mx > 0.40)
fin = cov & (x > 0.12) & (x < 0.26) & (z > 0.36) & (z < 0.54) & (s < 0.5) & (mx > 0.5)   # the armpit fin's cream paint
lace = ndi.binary_dilation(lace | fin, iterations=3) & cov
valid = cov & ~lace
out = img.copy()
w = ndi.gaussian_filter(valid.astype(float), 8)
fill = np.stack([ndi.gaussian_filter(img[..., c] * valid, 8) for c in range(3)], -1) / np.maximum(w, 1e-6)[..., None]
detail = img - np.stack([ndi.gaussian_filter(img[..., c], 3) for c in range(3)], -1)
shifted = np.roll(detail, 24, axis=1)
ok = np.roll(valid, 24, axis=1)
out[lace] = np.clip(fill[lace] + np.where(ok[lace][:, None], shifted[lace], 0), 0, 1)
Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save('textures/pm1d_basecolor.png')
print('TEXFIX back-lace and armpit-fin texels refilled', int(lace.sum()), 'fin', int(fin.sum()))
