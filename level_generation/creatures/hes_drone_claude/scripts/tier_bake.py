#!/usr/bin/env python3
"""Bake each tier's ramps into the base colour with the engine's rule (fs_model.sc: per region t = linear luminance
normalised over the range, colour = mix(colour, ramp(t), mask)), for previews and the three.js viewer GLBs:
work/tier_<variant>.png (2K) from textures/hdr_basecolor_2k.png, hdr_region_mask.png and hdr_ramps.json."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]; T = ROOT / 'textures'
W = np.array([0.2126, 0.7152, 0.0722], np.float32)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def apply(base_srgb, mask, ramps):
    c = lin(base_srgb); L = c @ W
    for k, r in enumerate(ramps):
        lo, hi = r['range']; t = np.clip((L - lo) / max(hi - lo, 1e-4), 0, 1)
        cs = np.array(r['colors'], np.float32); x = t * 15; i = np.minimum(x.astype(int), 14); f = (x - i)[..., None]
        rc = cs[i] * (1 - f) + cs[i + 1] * f
        c = c * (1 - mask[..., k:k + 1]) + rc * mask[..., k:k + 1]
    return srgb(c)


if __name__ == '__main__':
    R = json.load(open(T / 'hdr_ramps.json'))
    base = np.asarray(Image.open(T / 'hdr_basecolor_2k.png').convert('RGB'), np.float32) / 255
    # per channel: resizing an RGBA image premultiplies by alpha (and the trim channel A is mostly 0)
    mask = np.stack([np.asarray(ch.resize((2048, 2048), Image.BILINEAR), np.float32) / 255
                     for ch in Image.open(T / 'hdr_region_mask.png').convert('RGBA').split()], -1)
    body = next(m for m in R['materials'] if m['base'] == 'Casing_A')
    for v in R['variants']:
        out = apply(base, mask, body['ramps'][v])
        Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(ROOT / 'work' / f'tier_{v}.png')
        print('TIER', v)
