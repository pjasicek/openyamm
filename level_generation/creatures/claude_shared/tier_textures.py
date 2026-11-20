#!/usr/bin/env python3
"""Bake what the engine shows per tier: apply a ramps.json (claude_shared/region_variants.py format) to the shared base
colour with the shader's region-ramp maths (game/shaders/fs_model.sc), for offline previews and before/after
comparisons (Blender renders, contact sheets). Not a runtime asset.

Usage: tier_textures.py <base_graded.png> <region_mask.png> <ramps.json> <out_prefix> [material_index]
Writes <out_prefix>_<variant>.png for every variant of that material (default the first)."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

LUMA = np.array([0.2126, 0.7152, 0.0722])


def srgb_to_linear(v):
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(v):
    v = np.maximum(v, 0)
    return np.where(v <= 0.0031308, v * 12.92, 1.055 * v ** (1 / 2.4) - 0.055)


def apply(base_srgb, mask, ramps):
    """base_srgb H x W x 3 in 0..1, mask H x W x 4 in 0..1, ramps: list of {range, colors}. Returns sRGB."""
    out = srgb_to_linear(base_srgb)
    lum = out @ LUMA
    for channel, ramp in enumerate(ramps):
        lo, hi = ramp['range']
        t = np.clip((lum - lo) / max(hi - lo, 1e-4), 0, 1) * 15
        i0 = np.floor(t).astype(int); i1 = np.minimum(i0 + 1, 15); f = (t - i0)[..., None]
        colours = np.asarray(ramp['colors'])
        colour = colours[i0] * (1 - f) + colours[i1] * f
        w = mask[..., channel][..., None]
        out = out * (1 - w) + colour * w
    return linear_to_srgb(out)


def main():
    base_path, mask_path, ramps_path, prefix = sys.argv[1:5]
    material = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    base = np.asarray(Image.open(base_path).convert('RGB'), np.float64) / 255
    # Resize channel by channel: PIL resizes RGBA with premultiplied alpha, and an unused fourth region (A = 0)
    # would zero every channel.
    bands = Image.open(mask_path).convert('RGBA').split()
    size = (base.shape[1], base.shape[0])
    mask = np.stack([np.asarray(b if b.size == size else b.resize(size, Image.BILINEAR), np.float64) / 255
                     for b in bands], -1)
    config = json.loads(Path(ramps_path).read_text())
    entry = config['materials'][material]
    for variant in config['variants']:
        image = apply(base, mask, entry['ramps'][variant])
        path = f'{prefix}_{variant}.png'
        Image.fromarray((np.clip(image, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)
        print('WROTE', path)


if __name__ == '__main__':
    main()
