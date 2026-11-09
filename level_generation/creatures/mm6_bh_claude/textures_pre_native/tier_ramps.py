#!/usr/bin/env python3
"""Flying Eye tiers as one shared skin: per-region ramps straight from the native palette sprites
(CLAUDE_CREATURE_TEXTURES.md; method of mm6_spi1_claude/scripts/tier_ramps.py with three regions).

Native region coverage comes from the sprite package's 2x masks (../mm6_bh/masks_2x: R skin, G face/horns/teeth,
B iris), box-downsampled onto the native canvas, so the same pixels are sampled in every palette (669 / 670 / 671).
For each region the native pixels are sorted by luminance; ramp stop i sits at linear luminance lo + (hi - lo) * i / 15
of the graded shared base over that region, and takes the native colour at the same luminance quantile, brightened
per tier by GAIN for the sprites' baked shading. Writes textures/bh_region_mask.png and textures/bh_ramps.json."""
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
PACKAGE = ROOT.parent / 'mm6_bh'
PALETTES = {'bh_a': 669, 'bh_b': 670, 'bh_c': 671}
GAIN = {'bh_a': 1.4, 'bh_b': 1.4, 'bh_c': 1.4}
CHANNEL = {'skin': 0, 'face': 1, 'iris': 2}


def native_pixels(region, palette):
    pixels = []
    for mask_path in sorted((PACKAGE / 'masks_2x').glob('*.png')):
        frame_path = PACKAGE / 'native_variants' / f'{mask_path.stem}_{palette}.png'
        if not frame_path.exists():
            continue
        frame = np.asarray(Image.open(frame_path).convert('RGBA'), np.float64) / 255
        mask = Image.open(mask_path).convert('RGBA').getchannel(CHANNEL[region])
        mask = np.asarray(mask.resize((frame.shape[1], frame.shape[0]), Image.BOX), np.float64) / 255
        pixels.append(frame[..., :3][(mask > 0.6) & (frame[..., 3] > 0.5)])
    pixels = np.concatenate(pixels)
    return pixels[np.argsort(R.srgb_to_linear(pixels) @ R.LUMA)]


def main():
    base = R.load_srgb(T / 'bh_a_basecolor_graded.png')
    weights = np.load(T / 'bh_region_weights.npz')
    names = [str(n) for n in weights['names']]
    R.write_mask([np.asarray(weights[n], np.float64) for n in names], T / 'bh_region_mask.png')
    luminance = R.luminance(base)
    ramps = {variant: [] for variant in PALETTES}
    report = {}
    for name in names:
        lum = np.sort(luminance[np.asarray(weights[name]) > 0.9])
        lo, hi = np.percentile(lum, 0.5), np.percentile(lum, 99.5)
        stops = lo + (hi - lo) * np.arange(16) / 15
        quantiles = np.searchsorted(lum, stops) / len(lum)
        report[name] = {'texels': int(len(lum))}
        for variant, palette in PALETTES.items():
            native = native_pixels(name, palette)
            colours = []
            for q in quantiles:
                centre = int(np.clip(q, 0, 1) * (len(native) - 1)); half = max(len(native) // 200, 2)
                window = native[max(centre - half, 0):centre + half + 1]
                colours.append(R.srgb_to_linear(np.clip(np.median(window, 0) * GAIN[variant], 0, 1)))
            ramps[variant].append({'range': [round(float(lo), 6), round(float(max(hi, lo + 1e-3)), 6)],
                                   'colors': np.round(np.clip(colours, 0, 1), 6).tolist()})
            report[name][variant] = np.round(np.median(native, 0), 3).tolist()
    config = {'variants': list(PALETTES),
              'materials': [{'base': 'Eye_A', 'prefix': 'Eye', 'mask': 'bh_region_mask.png', 'regions': names,
                             'palettes': PALETTES, 'ramps': ramps, 'native_median_srgb': report}]}
    (T / 'bh_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
