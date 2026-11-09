#!/usr/bin/env python3
"""PBR textures of the reworked hanging brazier torch03, derived from CC0 Poly Haven scans (downloaded by
../../fire/scripts/fetch_textures.py into ../../fire/source/polyhaven/; derivation in ../../fire/scripts/pbr.py)
into textures/:

| set | Poly Haven source | use |
|---|---|---|
| t3_iron | rusty_metal_04 | pitted forged iron: the dish's flank, floor and finial |
| t3_paint | blue_metal_plate | the dish's blue-painted underside |
| t3_brass | rusty_metal_03 | the copper-brass rim and the chain ring |
| t3_ember | marble_rock_01 through a fire ramp (its cracks glow) | the glowing coal dome (lit, plus emission) |
| t3_chain | chain_basecolor.png (this batch's link strip) x rusty_metal_03 detail | the cut-out chain ribbons |

t3_chain keeps the procedural link strip's alpha and shading, multiplies in the brass scan's light and dark detail
and adds a normal map from the links' rounded relief (the blurred cut-out mask). The torch batch's other models keep
their textures (make_textures.py). Usage: make_pbr_textures.py"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'fire' / 'scripts'))
import pbr  # noqa: E402

OUT = HERE / 'textures'
EMBER_RAMP = [(0.0, (90, 18, 4)), (0.35, (180, 60, 14)), (0.65, (232, 118, 34)), (0.9, (252, 182, 72)),
              (1.0, (255, 222, 135))]
SETS = {
    't3_iron': dict(asset='rusty_metal_04', saturation=0.15, hue=(112, 108, 108), mean=0.2, contrast=2.0,
                    rough=(0.6, 0.35), rough_range=(0.5, 0.95), metal=0.25, normal_strength=3.0, size=256),
    't3_paint': dict(asset='blue_metal_plate', saturation=1.0, hue=None, mean=0.12, contrast=1.6,
                     rough=(0.8, 0.05), rough_range=(0.3, 0.8), metal=0.15, normal_strength=2.0, size=256),
    't3_brass': dict(asset='rusty_metal_03', saturation=0.0, hue=(200, 150, 95), mean=0.4, contrast=1.4,
                     rough=(0.6, 0.2), rough_range=(0.4, 0.8), metal=0.3, normal_strength=2.0, size=256),
    't3_ember': dict(asset='marble_rock_01', ramp=EMBER_RAMP, invert=True, rough=(0.3, 0.6),
                     rough_range=(0.6, 0.95), metal=0.0, normal_strength=1.4, size=256),
}


def chain():
    strip = np.asarray(Image.open(OUT / 'chain_basecolor.png').convert('RGBA')).astype(np.float64)
    h, w = strip.shape[:2]
    detail = pbr.base_colour('rusty_metal_03', 256, 0.0, None, 0.4, 1.4) @ pbr.LUMA
    detail = np.asarray(Image.fromarray(detail.astype(np.float32), 'F').resize((w, h), Image.BILINEAR))
    detail = np.clip(detail / detail.mean(), 0.55, 1.5)
    colour = pbr.linear(strip[..., :3]) * detail[..., None]
    alpha = strip[..., 3]
    # Rounded wire relief: the cut-out mask blurred, as height.
    mask = Image.fromarray(alpha.astype(np.uint8))
    height = np.asarray(mask.filter(ImageFilter.GaussianBlur(2.2))).astype(np.float64) / 255.0
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5 * 6.0
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5 * 6.0
    normal = np.stack([-dx, dy, np.ones_like(height)], -1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    rgba = np.dstack([pbr.srgb(colour) * 255, alpha])
    Image.fromarray((rgba + 0.5).clip(0, 255).astype(np.uint8), 'RGBA').save(OUT / 't3_chain_basecolor.png',
                                                                            optimize=True)
    Image.fromarray((normal * 127.5 + 127.5).astype(np.uint8)).save(OUT / 't3_chain_normal.png', optimize=True)
    rough = 0.3 + 0.25 * (1 - height)
    mr = np.dstack([np.zeros(rough.shape), rough, np.full(rough.shape, 0.3)])
    Image.fromarray((mr * 255 + 0.5).astype(np.uint8)).save(OUT / 't3_chain_mr.png', optimize=True)
    print('CHAIN', OUT / 't3_chain_basecolor.png')


def main():
    for name, spec in SETS.items():
        mean = pbr.derive(OUT, name, **spec)
        print('PBR', name, mean, 'sRGB', [round(float(v) * 255) for v in pbr.srgb(np.array(mean))])
    chain()


if __name__ == '__main__':
    main()
