#!/usr/bin/env python3
"""Bat tiers by palette transfer (../NATIVE_SHADING_TRANSFER.md, claude_shared/native_shading.py transfer_ramps),
replacing the fit of compose_bat.py's single-colour tier tints (claude_shared/fit_tier_regions.py).

Next to its sprites the 3D bat read too saturated and evenly orange in the wings, and its body lighter and more purple.
The sprites' wings run from dark brown at the bones to bright golden yellow, their body is dark grey-mauve. Two
regions on the shared tier-A skin: `membrane` (compose_bat.py) and `body` (fur and skin, the same in every tier).
For each ramp stop, the native pixels of that region nearest in luminance (palette 666) are read in each tier's
palette 666/667/668 (walk frames, all views). Native regions by colour on the 666 frames: membrane = saturated
amber, body = low saturation, not the red eyes or pale teeth. No brightness bake: the bat banks and flaps.
Writes textures/bat_region_mask.png (R membrane, G body) and textures/bat_ramps.json."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared'))
import region_variants as R
import native_shading as NS

ROOT = HERE.parent
T = ROOT / 'textures'
NATIVE = HERE.parents[1] / 'mm6_bat' / 'native_variants'
PALETTES = {'bat_a': 666, 'bat_b': 667, 'bat_c': 668}
GAIN = {'membrane': 1.2, 'body': 1.25}


def native_pixels():
    regions, pix = [], {p: [] for p in PALETTES.values()}
    for path in sorted(NATIVE.glob('batwa*_666.png')):
        ref = np.asarray(Image.open(path).convert('RGBA'), np.float64) / 255
        rgb = ref[..., :3]; hi, lo = rgb.max(-1), rgb.min(-1); sat = (hi - lo) / np.maximum(hi, 1e-6)
        hsv = np.asarray(Image.fromarray((rgb * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
        hue = hsv[..., 0] * 360
        alpha = ref[..., 3] > 0.5
        membrane = alpha & (hue > 20) & (hue < 60) & (sat > 0.45)
        red = alpha & (rgb[..., 0] > 2 * rgb[..., 1]) & (sat > 0.6) & (hi > 0.35)
        pale = alpha & (sat < 0.25) & (hi > 0.6)
        body = alpha & (sat < 0.4) & ~membrane & ~red & ~pale
        y, x = np.nonzero(membrane | body)
        regions.append(np.where(membrane[y, x], 0, 1))
        for p in PALETTES.values():
            tier = np.asarray(Image.open(str(path).replace('_666.png', f'_{p}.png')).convert('RGB'), np.float64) / 255
            pix[p].append(tier[y, x])
    return dict({f'p{p}': np.concatenate(v) for p, v in pix.items()}, region=np.concatenate(regions),
                region_names=np.array(['membrane', 'body']))


def main():
    base = R.load_srgb(T / 'bat_a_basecolor_graded.png')
    membrane = np.asarray(np.load(T / 'bat_region_weights.npz')['membrane'], np.float64)
    body = np.asarray(np.load(T / 'bat_body_weight.npz')['body'], np.float64)
    R.write_mask([membrane, body], T / 'bat_region_mask.png')
    pixels = native_pixels()
    ramps = NS.transfer_ramps(base, {'membrane': membrane}, pixels, {'membrane': 'membrane'}, PALETTES,
                              reference=666, gain=GAIN)
    # body by luminance rank (as mm6_spi1_claude/scripts/tier_ramps.py): the 3D body is brighter than every native
    # body pixel, so nearest-luminance matching only read the sprite's few highlights
    lum = R.luminance(base)[body > 0.9]
    lo, hi = np.percentile(lum, 0.5), np.percentile(lum, 99.5)
    quant = np.searchsorted(np.sort(lum), lo + (hi - lo) * np.arange(16) / 15) / len(lum)
    sel = pixels['region'] == 1
    order = np.argsort(R.srgb_to_linear(pixels['p666'][sel]) @ R.LUMA)
    for variant, palette in PALETTES.items():
        native = pixels[f'p{palette}'][sel][order]; half = max(len(native) // 100, 2); colours = []
        for q in quant:
            c = int(np.clip(q, 0, 1) * (len(native) - 1))
            colours.append(R.srgb_to_linear(np.clip(np.median(native[max(c - half, 0):c + half + 1], 0) * GAIN['body'], 0, 1)))
        ramps[variant].append({'range': [round(float(lo), 6), round(float(hi), 6)],
                               'colors': np.round(np.clip(colours, 0, 1), 6).tolist()})
    config = {'variants': list(PALETTES),
              'materials': [{'base': 'Bat_A', 'prefix': 'Bat', 'mask': 'bat_region_mask.png',
                             'regions': ['membrane', 'body'], 'palettes': PALETTES, 'ramps': ramps}]}
    (T / 'bat_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
    print('NATIVE pixels', {n: int((pixels['region'] == i).sum()) for i, n in enumerate(['membrane', 'body'])})


if __name__ == '__main__':
    main()
