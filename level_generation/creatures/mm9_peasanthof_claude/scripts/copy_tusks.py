#!/usr/bin/env python3
"""Copy tier A's painted lower tusks into another head set (same HeadUV): MM9's PeasantHOF1b also shows the half-orc
tusks, but her head retexture painted none. Tusk texels = A's head texels near the two mouth corners (rest positions
within 9 mm of a corner, 1.70..1.735 m high, front) that are ivory (saturation < 0.36, luminance > 170), closed, dilated
one texel and feathered 0.8 texel. Usage (project folder): copy_tusks.py <export glb> <src prefix> <dst prefix>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpart import texel_parts
glb, src, dst = sys.argv[1:4]
A = np.asarray(Image.open(f'textures/{src}_head_basecolor.png').convert('RGB'), float)
B = np.asarray(Image.open(f'textures/{dst}_head_basecolor.png').convert('RGB'), float)
pos, part, _ = texel_parts(glb, 'PeasantHOFHead', A.shape[0]); P = np.nan_to_num(pos)
lum = A @ np.array([0.299, 0.587, 0.114]); mx, mn = A.max(-1), A.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
near = np.zeros(lum.shape, bool)
for cx in (-0.032, 0.0137):
    near |= (np.abs(P[..., 0] - cx) < 0.009) & (P[..., 1] > 1.70) & (P[..., 1] < 1.735) & (P[..., 2] > 0.0)
m = near & (sat < 0.36) & (lum > 170)
m = ndimage.binary_closing(m, iterations=1)
w = ndimage.gaussian_filter(ndimage.binary_dilation(m, iterations=1).astype(float), 0.8) * near
out = B * (1 - w[..., None]) + A * w[..., None]
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(f'textures/{dst}_head_basecolor.png')
print('COPYTUSKS', src, '->', dst, 'texels', int(m.sum()))
