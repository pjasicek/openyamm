#!/usr/bin/env python3
"""work/impostor_*_raw.png -> work/impostor_basecolor.png (RGBA, colour dilated into transparent texels) and
work/impostor_normal.png (RGB, dilated the same way so mips never pull in a foreign normal)."""
import os
import numpy as np
from PIL import Image
from scipy import ndimage
W = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work')
albedo = np.asarray(Image.open(os.path.join(W, 'impostor_albedo_raw.png')).convert('RGBA')).copy()
normal = np.asarray(Image.open(os.path.join(W, 'impostor_normal_raw.png')).convert('RGBA')).copy()
inside = albedo[..., 3] >= 128
idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
albedo[..., :3] = albedo[..., :3][idx[0], idx[1]]
normal[..., :3] = normal[..., :3][idx[0], idx[1]]
Image.fromarray(albedo, 'RGBA').save(os.path.join(W, 'impostor_basecolor.png'))
Image.fromarray(normal[..., :3], 'RGB').save(os.path.join(W, 'impostor_normal.png'))
print('IMPOSTOR coverage', round(float(inside.mean()), 3))
