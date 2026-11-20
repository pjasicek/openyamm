#!/usr/bin/env python3
"""Spider tiers as one shared skin: ramps taken straight from the native palette sprites (CLAUDE_CREATURE_TEXTURES.md).

For each tier (palettes 822 brown / 823 dark blue / 824 dark red) the native body pixels of every frame (opaque, not
the red eyes, not the pale fangs; the same pixels in every palette) are sorted by luminance. Ramp stop i sits at
linear luminance lo + (hi - lo) * i / 15 of the graded shared base (lo/hi = 0.5/99.5 % over the chitin region); its colour is the native colour at the same
luminance quantile, brightened per tier by GAIN because sprites carry baked shading. So the base's stripes keep their order and
every tier takes its palette. Writes textures/spi1_region_mask.png and textures/spi1_ramps.json."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared'))
import region_variants as R

ROOT = HERE.parent
T = ROOT / 'textures'
NATIVE = ROOT.parent / 'mm6_spi1' / 'native_variants'
PALETTES = {'spi1_a': 822, 'spi1_b': 823, 'spi1_c': 824}
# Brightness over the native colours (sprites carry baked shading). The red tier is pure red (no green/blue), so it
# reads darkest in game and gets the most (user review 2026-10-08: "a tad too dark, mainly the red variant").
GAIN = {'spi1_a': 1.45, 'spi1_b': 1.6, 'spi1_c': 1.95}


def native_pixels(palette):
    """Body pixels of every frame in this palette. The eye/fang exclusion is found on the brown tier-A frame (eyes
    red, fangs pale) and applied at the same pixels in every palette, so all tiers sample the same body pixels."""
    pixels = []
    for path in sorted(NATIVE.glob(f'*_{PALETTES["spi1_a"]}.png')):
        reference = np.asarray(Image.open(path).convert('RGBA'), np.float64) / 255
        rgb_a = reference[..., :3]
        high, low = rgb_a.max(-1), rgb_a.min(-1)
        sat = (high - low) / np.maximum(high, 1e-6)
        red = (rgb_a[..., 0] > rgb_a[..., 1] * 1.8) & (rgb_a[..., 0] > 0.35) & (sat > 0.6)
        pale = (sat < 0.3) & (high > 0.45)
        keep = (reference[..., 3] > 0.5) & ~red & ~pale
        frame = np.asarray(Image.open(str(path).replace(f'_{PALETTES["spi1_a"]}.png', f'_{palette}.png')).convert(
            'RGBA'), np.float64) / 255
        pixels.append(frame[..., :3][keep])
    pixels = np.concatenate(pixels)
    return pixels[np.argsort(R.srgb_to_linear(pixels) @ R.LUMA)]


def main():
    base = R.load_srgb(T / 'spi1_a_basecolor_graded.png')
    weight = np.asarray(np.load(T / 'spi1_region_weights.npz')['chitin'], np.float64)
    R.write_mask([weight], T / 'spi1_region_mask.png')
    lum = R.luminance(base)[weight > 0.9]
    lo, hi = np.percentile(lum, 0.5), np.percentile(lum, 99.5)
    stops = lo + (hi - lo) * np.arange(16) / 15
    quantiles = np.searchsorted(np.sort(lum), stops) / len(lum)
    ramps, report = {}, {}
    for variant, palette in PALETTES.items():
        native = native_pixels(palette)
        colours = []
        for q in quantiles:
            centre = int(np.clip(q, 0, 1) * (len(native) - 1)); half = max(len(native) // 200, 2)
            window = native[max(centre - half, 0):centre + half + 1]
            colours.append(R.srgb_to_linear(np.clip(np.median(window, 0) * GAIN[variant], 0, 1)))
        ramps[variant] = [{'range': [round(float(lo), 6), round(float(hi), 6)],
                           'colors': np.round(np.clip(colours, 0, 1), 6).tolist()}]
        report[variant] = {'native_pixels': int(len(native)),
                           'native_median_srgb': np.round(np.median(native, 0), 3).tolist()}
    config = {'variants': list(PALETTES),
              'materials': [{'base': 'Spider_A', 'prefix': 'Spider', 'mask': 'spi1_region_mask.png',
                             'regions': ['chitin'], 'palettes': PALETTES, 'ramps': ramps, 'native': report}]}
    (T / 'spi1_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
    print(json.dumps({'range': [round(float(lo), 4), round(float(hi), 4)], 'native': report}))


if __name__ == '__main__':
    main()
