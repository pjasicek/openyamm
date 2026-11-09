#!/usr/bin/env python3
"""Grade creature base colours so features read like the sprites (which carry painted shading and saturated
palettes): multiply a baked AO map (smoothed: Cycles AO is grainy), damp the finest texel noise (Meshy pores and
grain read as dark speckles at game distance), add form-scale local contrast on luminance, a mild global contrast
and saturation.
Writes <name>_graded.png next to each input; the inputs stay untouched, so re-running never compounds.
Usage: grade_basecolor.py --ao ao.png [--ao-strength 0.7] [--local 0.6] [--contrast 1.12] [--saturation 1.25]
                          basecolor.png [...]"""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

parser = argparse.ArgumentParser()
parser.add_argument('--ao', required=True)
parser.add_argument('--ao-strength', type=float, default=0.7)
parser.add_argument('--local', type=float, default=0.6)
parser.add_argument('--local-sigma', type=float, default=16.0)
parser.add_argument('--fine', type=float, default=0.5, help='kept fraction of detail finer than --fine-sigma')
parser.add_argument('--fine-sigma', type=float, default=1.5)
parser.add_argument('--ao-sigma', type=float, default=2.0)
parser.add_argument('--contrast', type=float, default=1.12)
parser.add_argument('--saturation', type=float, default=1.25)
parser.add_argument('inputs', nargs='+')
args = parser.parse_args()
W = np.array([0.2126, 0.7152, 0.0722], np.float32)
ao_cache = {}


def ao_for(shape):
    """AO resized to the texture; texels outside the baked islands (black) take the nearest baked value, so mip
    levels do not pull dark borders into the islands."""
    if shape not in ao_cache:
        ao = np.asarray(Image.open(args.ao).convert('L').resize(shape[::-1], Image.BILINEAR), np.float32) / 255
        empty = ao <= 0.003
        if empty.any():
            _, (iy, ix) = ndimage.distance_transform_edt(empty, return_indices=True)
            ao = ao[iy, ix]
        ao_cache[shape] = ndimage.gaussian_filter(ao, args.ao_sigma)
    return ao_cache[shape]


for path in map(Path, args.inputs):
    rgb = np.asarray(Image.open(path).convert('RGB'), np.float32) / 255
    rgb = rgb * (1.0 - args.ao_strength * (1.0 - ao_for(rgb.shape[:2])))[..., None]
    lum = rgb @ W
    smooth = ndimage.gaussian_filter(lum, args.fine_sigma)
    damped = smooth + args.fine * (lum - smooth)
    rgb = rgb * (np.clip(damped, 0, 1) / np.maximum(lum, 1e-4))[..., None]
    lum = rgb @ W
    blurred = ndimage.gaussian_filter(lum, args.local_sigma)
    target = lum + args.local * (lum - blurred)
    median = float(np.median(lum))
    target = median + args.contrast * (target - median)
    rgb = rgb * (np.clip(target, 0, 1) / np.maximum(lum, 1e-4))[..., None]
    lum = rgb @ W
    rgb = lum[..., None] + args.saturation * (rgb - lum[..., None])
    out = path.with_name(path.stem + '_graded.png')
    Image.fromarray(np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8)).save(out, optimize=True)
    print('GRADED', out)
