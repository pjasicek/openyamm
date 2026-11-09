#!/usr/bin/env python3
"""Apply tier pm6_a's mask + ramp to the installed Annud base colours exactly as fs_model.sc does (linear luminance
lookup, 16 stops, mix by the mask's R channel), for review textures. Usage (tier_m6a/): preview_ramp.py <installed glb>
Writes work/preview_<image>_pm6a.png for the body and head base colours."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tier_mask_ramp import glb_image, lin  # noqa: E402

glb = sys.argv[1]
r = json.load(open('textures/annud_m6a_ramps.json'))['ramp']
lo, hi = r['range']; cols = np.array(r['colors'])


def to_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


for name, mask in (('annud_tp_basecolor_graded', 'annud_m6a_region_mask'),
                   ('annud_tp_head_basecolor_export', 'annud_m6a_head_region_mask')):
    im = np.asarray(glb_image(glb, name)) / 255.0
    # R channel only: PIL premultiplies RGBA by alpha when resizing, and the mask's alpha (region 4) is 0.
    m = np.asarray(Image.open(f'textures/{mask}.png').getchannel(0).resize(im.shape[1::-1], Image.BILINEAR)) / 255.0
    L = lin(im); lum = L @ np.array([0.2126, 0.7152, 0.0722])
    t = np.clip((lum - lo) / (hi - lo), 0, 1) * 15
    i0 = np.floor(t).astype(int).clip(0, 14); f = (t - i0)[..., None]
    ramp = cols[i0] * (1 - f) + cols[i0 + 1] * f
    out = to_srgb(L * (1 - m[..., None]) + ramp * m[..., None])
    Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(f'work/preview_{name}_pm6a.png')
    print('PREVIEW', name, 'masked mean sRGB before', (im[m > 0.8].mean(0) * 255).round(),
          'after', (out[m > 0.8].mean(0) * 255).round())
