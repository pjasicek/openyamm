#!/usr/bin/env python3
"""Native shading transfer on the spider (../NATIVE_SHADING_TRANSFER.md), between compose_spi1.py and the grade.

Next to its sprites the 3D spider read lighter, flatter and more strongly banded: the sprites are lit from above (the
abdomen top bright, the underside and lower legs dark) and their leg bands are soft. Profile: brightness by height of
every opaque body pixel (not the red eyes, not the pale fangs) in the native standing views (spi1sta0..4, palette 822;
height 0 at the feet, 1 at the top of the abdomen). Texels of the chitin region take that brightness at their rest-pose
height times their own local detail raised to DETAIL (softer bands), blended by AMOUNT; the existing tier ramps
(tier_ramps.py: native colours by luminance quantile, per-tier gains) then recolour it, so the overall brightness of
each tier stays as reviewed and only where light and dark sit changes.
Reads textures_pre_native/spi1_a_basecolor.png (the compose output), writes textures/spi1_a_basecolor.png."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE.parents[1] / 'mm6_gob_claude' / 'scripts'))
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared'))
import compose_textures_v2 as C
import native_shading as NS

NATIVE = HERE.parents[1] / 'mm6_spi1' / 'native_variants'
FRAMES = [f'spi1sta{i}' for i in range(5)]
AMOUNT, DETAIL, SIGMA, BIN = 0.7, 0.5, 10.0, 0.05


def profile():
    coords, lums = [], []
    for name in FRAMES:
        im = np.asarray(Image.open(NATIVE / f'{name}_822.png').convert('RGBA'), np.float64) / 255
        rgb = im[..., :3]; hi, lo = rgb.max(-1), rgb.min(-1); sat = (hi - lo) / np.maximum(hi, 1e-6)
        red = (rgb[..., 0] > rgb[..., 1] * 1.8) & (rgb[..., 0] > 0.35) & (sat > 0.6)
        pale = (sat < 0.3) & (hi > 0.45)
        keep = (im[..., 3] > 0.5) & ~red & ~pale
        rows = np.nonzero((im[..., 3] > 0.5).any(1))[0]
        y, x = np.nonzero(keep)
        coords.append((rows.max() - y) / (rows.max() - rows.min())); lums.append(NS.srgb_luminance(rgb[y, x]))
    coords, lums = np.concatenate(coords), np.concatenate(lums)
    bins = np.round(np.arange(0, 1 + BIN / 2, BIN), 6)
    curve, _ = NS._binned(coords, lums, bins, BIN)
    return bins, curve


def main():
    bins, curve = profile()
    data = np.load(ROOT / 'work' / 'uv3d.npz')
    part_map, xyz = C.rasterise(data)
    region = np.asarray(np.load(ROOT / 'textures' / 'spi1_region_weights.npz')['chitin']) > 0.5
    base = C.load(str(ROOT / 'textures_pre_native' / 'spi1_a_basecolor.png'))
    region &= part_map >= 0
    z = data['xyz'][..., 2]
    coord = NS.texel_coordinate(xyz, 'height', z_range=(float(z.min()), float(z.max())))
    out = base.copy()
    NS.shade(out, coord, region, {'bins': bins, 'luminance': curve}, detail_strength=DETAIL,
             detail=NS.detail_of(base, SIGMA), amount=AMOUNT)
    Image.fromarray(np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)).save(ROOT / 'textures' / 'spi1_a_basecolor.png')
    print('SHADED', int(region.sum()), 'texels; profile', np.round(curve[::4], 3).tolist())


if __name__ == '__main__':
    main()
