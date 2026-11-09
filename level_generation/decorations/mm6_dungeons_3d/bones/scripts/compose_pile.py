#!/usr/bin/env python3
"""Texture set of the baked skull pile from the high-to-low bakes (bake_pile.py): base colour = baked colour x
(1 - AO_STRENGTH (1 - baked AO)) x an optional baked top light (LIGHT), optionally graded toward the native sprite (texture level only: the base's
luminance histogram over the covered texels matched to the sprite's at GRADE, and its colour pulled toward the
sprite's luminance-to-colour table at CHROMA), the baked tangent normals, and a flat metallic-roughness (bone: rough
ROUGHNESS, no metal). Writes textures/<prefix>_{basecolor,normal,mr}.png at <size>.
Usage: compose_pile.py <prefix> <bake size> <out size> [ao strength] [grade 0..1] [chroma 0..1] [light 0..1]"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LUMA = np.array([0.2126, 0.7152, 0.0722])
prefix, bake, size = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
AO_STRENGTH = float(sys.argv[4]) if len(sys.argv) > 4 else 0.85
GRADE = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
CHROMA = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
LIGHT = float(sys.argv[7]) if len(sys.argv) > 7 else 0.0
ROUGHNESS = 0.78
EXPOSED = 0.6
CORNER = 0.875                     # add_far_lod.py: LOD0's charts fill [0, CORNER]^2, the far mesh's the rest
DENOISE = float(os.environ.get('DENOISE', '0.7'))
NORMAL_SIZE = int(os.environ.get('NORMAL_SIZE', '1024'))   # most detail lives in the graded colour
WORK = os.path.join(HERE, 'work')
TEXTURES = os.path.join(HERE, 'textures')


def load(name, mode='RGB'):
    return np.asarray(Image.open(os.path.join(WORK, f'pilebake_{name}_{bake}.png')).convert(mode), np.float64) / 255


base = load('base')
ao = load('ao', 'L')
covered = ndimage.binary_erosion(base.sum(-1) > 0.02, iterations=1)
# Meshy's bone-pore grain turns into speckle once graded: keep DENOISE of it blurred (sigma 1.2 texels, inside the
# charts only so no background bleeds in).
weight = ndimage.gaussian_filter(covered.astype(float), 1.2)
smooth = np.stack([ndimage.gaussian_filter(base[..., c] * covered, 1.2) for c in range(3)], -1) / np.maximum(
    weight, 1e-3)[..., None]
base = np.where(covered[..., None], base * (1 - DENOISE) + smooth * DENOISE, base)
out = base * (1 - AO_STRENGTH * (1 - ao))[..., None]
if LIGHT > 0:
    # The sprite's painted light, per texel from the high mesh's object-space normal: from above and outward at
    # every azimuth (the pile is seen from all sides), mixed in at LIGHT.
    n = load('objnormal') * 2 - 1
    light = np.clip(0.8 * n[..., 2] + 0.6 * np.linalg.norm(n[..., :2], axis=-1), 0, 1)
    out = out * ((1 - LIGHT) + LIGHT * (0.25 + 0.75 * light))[..., None]
if GRADE > 0:
    native = np.asarray(Image.open(os.path.join(HERE, 'native', 'sklplrev_native_embedded.png')).convert('RGBA'),
                        np.float64)
    pixels = native[native[..., 3] > 0][:, :3] / 255
    nlum = pixels @ LUMA
    lum = out @ LUMA
    q = np.linspace(0, 1, 257)
    # Fitted on the exposed texels (AO above EXPOSED: those an outside view shows); the gap texels fall below.
    h, w = lum.shape
    rows, cols = np.mgrid[0:h, 0:w]
    near = (cols < w * CORNER) & (rows >= h * (1 - CORNER))      # LOD0's charts (image rows run top-down)
    exposed = covered & (ao > EXPOSED) & near
    target = np.interp(lum, np.quantile(lum[exposed], q), np.quantile(nlum, q))
    tone = os.path.join(WORK, 'pilebake_tone.npz')
    if os.path.exists(tone):                       # pile_tone.py-style correction from the rendered front view
        curve = np.load(tone)
        target = np.interp(target, curve['before'], curve['after'])
    target = lum + (target - lum) * GRADE
    scale = target / np.maximum(lum, 1e-4)
    graded = out * scale[..., None]
    if CHROMA > 0:
        bins = np.linspace(0, 1, 33); centres = (bins[:-1] + bins[1:]) / 2
        index = np.clip(np.digitize(nlum, bins) - 1, 0, 31)
        table = np.array([pixels[index == k].mean(0) if (index == k).any() else [np.nan] * 3 for k in range(32)])
        for c in range(3):
            good = ~np.isnan(table[:, c])
            table[:, c] = np.interp(centres, centres[good], table[good, c])
        table = ndimage.gaussian_filter1d(table, 1.5, axis=0)
        tint = np.stack([np.interp(target, centres, table[:, c]) for c in range(3)], -1)
        tint *= (target / np.maximum(tint @ LUMA, 1e-4))[..., None]
        graded = graded * (1 - CHROMA) + tint * CHROMA
    out = np.where(covered[..., None], graded, out)
out = np.clip(out, 0, 1)


def save(array, name, out_size=None):
    out_size = out_size or size
    image = Image.fromarray(np.round(array * 255).astype(np.uint8))
    if out_size != bake:
        image = image.resize((out_size, out_size), Image.LANCZOS)
    image.save(os.path.join(TEXTURES, f'{prefix}_{name}.png'))


save(out, 'basecolor')
save(load('normal'), 'normal', NORMAL_SIZE)
mr = np.zeros((64, 64, 3)); mr[..., 0] = 1.0; mr[..., 1] = ROUGHNESS      # uniform: a small image is enough
Image.fromarray(np.round(mr * 255).astype(np.uint8)).save(os.path.join(TEXTURES, f'{prefix}_mr.png'))
print('COMPOSED', prefix, size, 'mean', np.round(out[covered].mean(0) * 255).tolist(), 'median lum',
      round(float(np.median(out[covered] @ LUMA)), 3))
