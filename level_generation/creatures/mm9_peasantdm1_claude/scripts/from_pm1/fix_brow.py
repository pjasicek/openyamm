#!/usr/bin/env python3
"""Brow and upper-lid band (2026-11-01, viewer shots from party height): the head retexture painted the band between
the eyes and the brows (rest height 1.652-1.672 m, the front of the face) as one flat tan/orange patch with a hard
outline, which read as a mask round the eyes from above. Inside the band the broad colour (Gaussian sigma 12 texels at
2K) moves 60 % toward the tier's own forehead skin x 0.85 (an eyelid in the brow's shade), the fine detail (brow hairs,
lid creases) stays; the weight ramps over 5 mm at the band's top and bottom and over 1 cm at its sides, so no new
edge appears. Run after fix_neck.py (works on the current head base colour; backup <prefix>_head_basecolor_prebrow.png
on the first run). Usage (project folder): fix_brow.py <export glb> <prefix> [...]"""
import sys, shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
glb, prefixes = sys.argv[1], sys.argv[2:]
N = 2048
pos, cov = texel_positions(glb, 'PeasantM1Head', N)
x, y, z = (np.nan_to_num(pos[..., i]) for i in range(3))
front = cov & (z > 0.03)


def ramp(v, a, b):
    return np.clip((v - a) / (b - a), 0, 1)


w = front * ramp(y, 1.647, 1.652) * (1 - ramp(y, 1.672, 1.677)) * (1 - ramp(np.abs(x), 0.06, 0.07))
w = ndimage.gaussian_filter(w, 1.5) * cov
fore = front & (y > 1.672) & (y < 1.688) & (np.abs(x) < 0.05)
for p in prefixes:
    f = Path(f'textures/{p}_head_basecolor.png')
    bk = Path(f'textures/{p}_head_basecolor_prebrow.png')
    if not bk.exists():
        shutil.copyfile(f, bk)
    img = np.asarray(Image.open(bk).convert('RGB'), float)
    ref = np.median(img[fore], 0) * 0.85
    # broad colour of the band from island texels only (normalised convolution), so gutters do not leak in
    m = cov.astype(float)
    low = ndimage.gaussian_filter(img * m[..., None], (12, 12, 0)) / np.maximum(ndimage.gaussian_filter(m, 12), 1e-3)[..., None]
    out = img + (ref[None, None] - low) * (0.6 * w)[..., None]
    near = ndimage.binary_dilation(w > 0.02, iterations=8) & ~cov
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out[near] = out[iy[near], ix[near]]
    Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f)
    print('FIXBROW', p, 'forehead ref x0.85', ref.round(), 'band texels', int((w > 0.5).sum()))
