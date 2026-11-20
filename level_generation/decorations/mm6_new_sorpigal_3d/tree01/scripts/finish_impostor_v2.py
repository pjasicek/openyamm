#!/usr/bin/env python3
"""work_v2/impostor_*_raw.png -> work_v2/impostor_basecolor.png (RGBA, colour dilated into transparent texels) and
work_v2/impostor_normal.png (RGB, dilated the same way so mips never pull in a foreign normal). The cutout grows by
2 px and its albedo takes IMPOSTOR_TONE."""
import os
import numpy as np
from PIL import Image
from scipy import ndimage
W = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work_v2')
albedo = np.asarray(Image.open(os.path.join(W, 'impostor_albedo_raw.png')).convert('RGBA')).copy()
normal = np.asarray(Image.open(os.path.join(W, 'impostor_normal_raw.png')).convert('RGBA')).copy()
inside = albedo[..., 3] >= 128
# grow the cutout by 2 px (of 1024): the far tree keeps the 3D levels' coverage once mipmapped down to ~150 px
inside = ndimage.binary_dilation(inside, iterations=2)
albedo[..., 3] = np.where(inside, 255, 0)
idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
albedo[..., :3] = albedo[..., :3][idx[0], idx[1]]
normal[..., :3] = normal[..., :3][idx[0], idx[1]]
# Calibrated in lod_check_v2.py (engine-like lighting): at ~150 px the 3D levels' mipmapped alpha lets darker interior
# through, which one front-most cutout does not; linear tone on the cutout's albedo matches the 3D levels' mean.
IMPOSTOR_TONE = np.array([0.94, 0.80, 1.02])
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)
albedo[..., :3] = (np.clip(srgb(lin(albedo[..., :3] / 255.0) * IMPOSTOR_TONE), 0, 1) * 255 + 0.5).astype(np.uint8)
Image.fromarray(albedo, 'RGBA').save(os.path.join(W, 'impostor_basecolor.png'))
Image.fromarray(normal[..., :3], 'RGB').save(os.path.join(W, 'impostor_normal.png'))
print('IMPOSTOR coverage', round(float(inside.mean()), 3))
