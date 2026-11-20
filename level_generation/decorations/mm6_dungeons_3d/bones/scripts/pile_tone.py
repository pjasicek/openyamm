#!/usr/bin/env python3
"""Tone correction for the instanced pile: the luminance quantiles of the flat front render (review/shape/
pile_close.png, pile_closeup.py) against the native sprite's, composed with any earlier correction, written to
work/pile_tone.npz (pairs of luminance before -> after) for build_skullpile_inst.py. Usage: pile_tone.py [--reset|--update] [curve file in work/, default pile_tone.npz]"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LUMA = np.array([0.2126, 0.7152, 0.0722])
path = os.path.join(HERE, 'work', sys.argv[2] if len(sys.argv) > 2 else 'pile_tone.npz')
if len(sys.argv) > 1 and sys.argv[1] == '--reset':
    if os.path.exists(path):
        os.remove(path)
    sys.exit()


def lum(image_path):
    a = np.asarray(Image.open(image_path).convert('RGBA'), np.float64) / 255
    return a[a[..., 3] > 0.9][:, :3] @ LUMA


q = np.linspace(0, 1, 65)
model = np.quantile(lum(os.path.join(HERE, 'review', 'shape', 'pile_close.png')), q)
native = np.quantile(lum(os.path.join(HERE, 'native', 'sklplrev_native_embedded.png')), q)
if os.path.exists(path):
    old = np.load(path)
    before = old['before']
    after = np.interp(np.interp(old['after'], model, native), [0, 1], [0, 1])
else:
    before, after = model, native
before = np.maximum.accumulate(before); after = np.maximum.accumulate(after)
np.savez(path, before=before, after=after)
print('TONE model median', round(float(model[32]), 3), 'native median', round(float(native[32]), 3))
