#!/usr/bin/env python3
"""Far-level maps to 512²: the impostor (LOD3, shown below ~160 px) and the LOD2 clump atlas (~160-250 px) gain
nothing from 1024², and each species carries its own copy (the bark and leaf maps are shared by the engine).
Colour maps are already dilated, so RGB resizes directly; alpha is rescaled to keep the 1024² cutout coverage at the
0.5 alpha test, so the far tree does not thin out. Normal maps are renormalized. Usage: shrink_far_maps.py <id>"""
import os, sys
import numpy as np
from PIL import Image
import common

SIZE = 512
SPEC = common.load(sys.argv[1]); W = SPEC["work"]
# MM7 change: a bare tree's impostor keeps 1024² (its thin twigs thicken into blobs when the coverage is restored)


def resize(channel):
    return np.asarray(Image.fromarray(channel.astype(np.float32), 'F').resize((SIZE, SIZE), Image.LANCZOS))


def shrink_cutout(path):
    pixels = np.asarray(Image.open(path).convert('RGBA')).astype(np.float32) / 255.0
    coverage = float((pixels[..., 3] >= 0.5).mean())
    out = np.stack([resize(pixels[..., c]) for c in range(4)], 2).clip(0.0, 1.0)
    low, high = 0.5, 4.0
    for _ in range(40):                      # alpha scale that restores the coverage at the cutoff
        scale = 0.5 * (low + high)
        if float((out[..., 3] * scale >= 0.5).mean()) < coverage:
            low = scale
        else:
            high = scale
    out[..., 3] = (out[..., 3] * high).clip(0.0, 1.0)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8), 'RGBA').save(path)
    return coverage, float((out[..., 3] >= 0.5).mean())


def shrink_normal(path):
    pixels = np.asarray(Image.open(path).convert('RGB')).astype(np.float32) / 255.0 * 2.0 - 1.0
    out = np.stack([resize(pixels[..., c]) for c in range(3)], 2)
    out /= np.maximum(np.linalg.norm(out, axis=2, keepdims=True), 1e-6)
    Image.fromarray(((out * 0.5 + 0.5) * 255 + 0.5).clip(0, 255).astype(np.uint8), 'RGB').save(path)


for stem in ('clumps',) if SPEC['season'] == 'bare' else ('impostor', 'clumps'):
    colour = os.path.join(W, f'{stem}_basecolor.png')
    if not os.path.exists(colour) or Image.open(colour).size[0] <= SIZE:
        continue
    before, after = shrink_cutout(colour)
    shrink_normal(os.path.join(W, f'{stem}_normal.png'))
    print('SHRINK', stem, SIZE, 'coverage', round(before, 4), '->', round(after, 4))
