#!/usr/bin/env python3
"""PBR textures of the reworked fire fixtures (brazier pair, cauldron, candle), derived from CC0 Poly Haven scans
(fetch_textures.py; derivation in pbr.py) into fire/textures/ph_*, and their linear means into textures/means.json
(the COLOR_0 tints bring each material's mean to the measured native sprite colour).

| set | Poly Haven source | use |
|---|---|---|
| ph_iron | rust_coarse_01 | cast iron: the cauldron pot |
| ph_ironpit | rusty_metal_04 (higher contrast) | pitted forged iron: brazier bowl and chains, candlestick foot, wick |
| ph_pewter | rusty_metal_02 | the candle's drip pan |
| ph_rock | marble_rock_01 | the cauldron's pink-grey cracked stones |
| ph_wax | leather_white (colour, grain) | candle wax: a fine soft grain, cream, semi-gloss |
| ph_charwood | bark_brown_02 | charred logs under the cauldron |
| ph_charcoal | marble_rock_02 | charcoal lumps on the ember beds: dark, cracked, semi-matte |
| ph_ember | marble_rock_01 through a fire ramp (its cracks glow) | glowing ember beds (lit, plus constant emission) |

Usage: make_pbr_textures.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pbr  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / 'textures'
EMBER_RAMP = [(0.0, (70, 12, 4)), (0.35, (165, 50, 12)), (0.65, (225, 105, 28)), (0.9, (250, 170, 60)),
              (1.0, (255, 215, 120))]
SETS = {
    # Cast iron, mottled like the native pot (luminance percentiles 5/25/50/75 of the 95th: 0.11/0.29/0.51/0.66).
    'ph_iron': dict(asset='rust_coarse_01', saturation=0.0, hue=None, mean=0.2, contrast=3.2,
                    rough=(0.8, 0.1), rough_range=(0.35, 0.9), metal=0.25, normal_strength=2.5),
    # Pitted forged iron: the same scan with the native brazier bowl's and candlestick's much wider light spread
    # (5th / 95th luminance percentile about 0.05).
    'ph_ironpit': dict(asset='rusty_metal_04', saturation=0.15, hue=(112, 108, 108), mean=0.2, contrast=2.2,
                       rough=(0.9, 0.0), rough_range=(0.3, 0.85), metal=0.25, normal_strength=3.0, size=256),
    # Worn pewter: the scan's spots flattened to faint tarnish, semi-gloss.
    'ph_pewter': dict(asset='rusty_metal_02', saturation=0.0, hue=None, mean=0.42, contrast=0.45,
                      rough=(0.5, 0.05), rough_range=(0.22, 0.5), metal=0.35, normal_strength=1.5, size=256),
    'ph_rock': dict(asset='marble_rock_01', saturation=0.25, hue=(205, 150, 140), mean=0.55, contrast=1.15,
                    rough=(0.6, 0.35), rough_range=(0.5, 0.95), metal=0.0, normal_strength=1.4),
    'ph_wax': dict(asset='leather_white', saturation=0.0, hue=(246, 238, 222), mean=0.86, contrast=3.0,
                   rough=(0.5, 0.2), rough_range=(0.3, 0.6), metal=0.0, normal_strength=2.0, size=256),
    'ph_charwood': dict(asset='bark_brown_02', saturation=0.3, hue=(80, 45, 30), mean=0.07, contrast=1.4,
                        rough=(0.4, 0.55), rough_range=(0.6, 0.98), metal=0.0, normal_strength=1.3, size=256),
    'ph_charcoal': dict(asset='marble_rock_02', saturation=0.1, hue=(70, 60, 56), mean=0.06, contrast=1.6,
                        rough=(0.5, 0.35), rough_range=(0.45, 0.9), metal=0.0, normal_strength=1.8, size=256),
    'ph_ember': dict(asset='marble_rock_01', ramp=EMBER_RAMP, invert=True, rough=(0.3, 0.6),
                     rough_range=(0.6, 0.95), metal=0.0, normal_strength=1.4, size=256),
}


def main():
    means = {}
    for name, spec in SETS.items():
        means[name] = pbr.derive(OUT, name, **spec)
        print('PBR', name, means[name], 'sRGB', [round(float(v) * 255) for v in pbr.srgb(means[name])])
    pbr.write_means(OUT / 'means.json', means)


if __name__ == '__main__':
    main()
