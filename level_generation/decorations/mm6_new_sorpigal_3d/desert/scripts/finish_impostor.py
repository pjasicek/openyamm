#!/usr/bin/env python3
"""work/<id>/impostor_*_raw.png -> impostor_basecolor.png (RGBA) and impostor_normal.png (RGB), box-filtered to
half size (512 px on the long side), cut out at alpha 0.5 (not grown: the spiky outlines already cover more than
the 3D levels at a distance), colour and normal dilated into the transparent texels (mips never pull in a foreign colour), and the
albedo scaled by the per-plant linear tone from impostor_tone.json (calibrate_impostor.py).
Usage: finish_impostor.py <id>"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desert_common as dc
SID = sys.argv[1]; W = dc.work(SID)
_tones = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'impostor_tone.json')
TONE = np.asarray(json.load(open(_tones)).get(SID, [1.0, 1.0, 1.0]) if os.path.exists(_tones) else [1.0, 1.0, 1.0])


def load(name):
    return np.asarray(Image.open(os.path.join(W, name)).convert('RGBA')).astype(np.float64) / 255.0


albedo = load('impostor_albedo_raw.png'); normal = load('impostor_normal_raw.png')
h, w = albedo.shape[:2]
alpha = albedo[..., 3]


def down(x):
    return x[:h // 2 * 2, :w // 2 * 2].reshape(h // 2, 2, w // 2, 2, *x.shape[2:]).mean((1, 3))


a = down(alpha)
CUT = 0.75          # a little inside the 3D outline: alpha-tested leaf cards lose their thinnest tips in the far mips
rgb = down(albedo[..., :3] * alpha[..., None]) / np.maximum(a, 1e-4)[..., None]
nrm = down(normal[..., :3] * alpha[..., None]) / np.maximum(a, 1e-4)[..., None]
inside = a >= CUT
_, (iy, ix) = ndimage.distance_transform_edt(~inside, return_indices=True)
rgb = rgb[iy, ix]; nrm = nrm[iy, ix]
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)
rgb = np.clip(srgb(lin(rgb) * TONE), 0, 1)
Image.fromarray(np.dstack([(rgb * 255 + 0.5).astype(np.uint8), np.where(inside, 255, 0).astype(np.uint8)]), 'RGBA').save(
    os.path.join(W, 'impostor_basecolor.png'))
Image.fromarray((np.clip(nrm, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(os.path.join(W, 'impostor_normal.png'))
print('IMPOSTOR', SID, (w // 2, h // 2), 'coverage', round(float(inside.mean()), 3), 'tone', TONE.tolist())
