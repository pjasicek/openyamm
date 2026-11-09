#!/usr/bin/env python3
"""Native shading transfer on the cockatrice body (../NATIVE_SHADING_TRANSFER.md), between compose_ckt.py and the
grade. Next to its sprites the body read lighter and flatter: the sprites are dark brown with light from above
(shoulders and chest top bright, belly, thighs and tail base dark).

Profile: native standing front and back views (cktstda0, cktstda4; palette 680, the body is the same brown in every
tier), brown feather pixels (hue 0-45 degrees, saturation 0.25+, not the bright orange legs, not the wing membrane of
the restored mask) in the central column of the silhouette; coordinate = height from the feet (0) to the top of the
brown neck under the pink head (1); median sRGB luminance per bin.
Texels: feathers (compose classes 2) of the body, tail and neck (uv3d parts 0, 3, 4; wings and legs excluded: they
swing, and the legs are scaly orange), same coordinate from the rest-pose z (0 at the lowest vertex, 1 at the top of
the body/neck texels). The body becomes a tier region of its own: its texels become the native luminance at their height x their own local
detail, as grey (NS.shade, blended by AMOUNT), and tier_ramps.py gives the region a ramp whose colours are the same
native body pixels read in each palette (NS.transfer_ramps; the body is the same brown in every tier). A first pass that
only rescaled the brightness and kept Meshy's orange-red hue barely changed the look: the gap was colour as much as
shading.
Reads the pristine compose output textures_pre_native/ckt_a_basecolor.png, writes textures/ckt_a_basecolor.png;
grade_basecolor.py (defaults) follows as before. Preview: review/native_shading/profile_body.png."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE.parents[1] / 'mm6_gob_claude' / 'scripts'))
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared'))
import compose_textures_v2 as C
import native_shading as NS

NATIVE = HERE.parents[1] / 'mm6_ckt'
FRAMES, PALETTE = ['cktstda0', 'cktstda4'], 680
PALETTES = [680, 681, 682]
AMOUNT, SIGMA = 0.85, 12.0
BIN = 0.04


def native_profile():
    coords, lums = [], []; pix = {p: [] for p in PALETTES}
    for name in FRAMES:
        im = np.asarray(Image.open(NATIVE / 'native_variants' / f'{name}_{PALETTE}.png').convert('RGBA'), np.float64) / 255
        mask = np.asarray(Image.open(NATIVE / 'masks_2x' / f'{name}.png').convert('RGBA').resize(
            (im.shape[1], im.shape[0]), Image.BOX), np.float64) / 255
        alpha = im[..., 3] > 0.5
        hsv = np.asarray(Image.fromarray((im[..., :3] * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
        h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
        brown = alpha & ((h < 45) | (h > 345)) & (s > 0.25) & (v < 0.62) & (mask[..., 0] < 0.4)
        xs = np.nonzero(alpha)[1]; cx, width = (xs.min() + xs.max()) / 2, xs.max() - xs.min()
        central = np.abs(np.arange(im.shape[1]) - cx)[None, :] < 0.14 * width
        body = brown & central
        rows = np.nonzero(body.any(1))[0]
        feet = np.nonzero(alpha.any(1))[0].max(); top = rows.min()
        y, x = np.nonzero(body)
        coords.append((feet - y) / (feet - top)); lums.append(NS.srgb_luminance(im[y, x, :3]))
        for p in PALETTES:
            tier = np.asarray(Image.open(NATIVE / 'native_variants' / f'{name}_{p}.png').convert('RGB'), np.float64) / 255
            pix[p].append(tier[y, x])
    coords, lums = np.concatenate(coords), np.concatenate(lums)
    pix = {p: np.concatenate(v) for p, v in pix.items()}
    bins = np.round(np.arange(0, 1 + BIN / 2, BIN), 6)
    curve, known = NS._binned(coords, lums, bins, BIN)
    return bins, curve, len(coords), pix


def main():
    bins, curve, n, pix = native_profile()
    np.savez_compressed(ROOT / 'work' / 'native_shading' / 'body_pixels.npz', region=np.zeros(len(pix[PALETTES[0]]), int),
                        region_names=np.array(['body']), **{f'p{p}': v for p, v in pix.items()})
    data = np.load(ROOT / 'work' / 'uv3d.npz')
    part_map, xyz = C.rasterise(data)
    classes = np.asarray(Image.open(ROOT / 'textures' / 'ckt_material_classes.png').resize(part_map.shape[::-1],
                                                                                            Image.NEAREST))
    base = C.load(str(ROOT / 'textures_pre_native' / 'ckt_a_basecolor.png'))
    region = (classes == 2) & np.isin(part_map, (0, 3, 4))
    z0 = float(data['xyz'][..., 2].min())
    z1 = float(np.percentile(xyz[region][:, 2], 99.5))
    coord = NS.texel_coordinate(xyz, 'height', z_range=(z0, z1))
    lum = NS.srgb_luminance(base)
    out = base.copy()
    NS.shade(out, coord, region, {'bins': bins, 'luminance': curve}, detail=NS.detail_of(base, SIGMA), amount=AMOUNT)
    weight = ndimage.gaussian_filter(region.astype(np.float32), 1.0)
    np.savez_compressed(ROOT / 'textures' / 'ckt_body_weight.npz', body=weight)
    Image.fromarray(np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)).save(ROOT / 'textures' / 'ckt_a_basecolor.png')
    review = ROOT / 'review' / 'native_shading'; review.mkdir(parents=True, exist_ok=True)
    strip = np.repeat(np.repeat(np.nan_to_num(curve)[::-1, None], 60, 1), 6, 0)
    Image.fromarray((np.clip(strip, 0, 1) * 255).astype(np.uint8)).save(review / 'profile_body.png')
    before = float(np.median(lum[region])); after = float(np.median(NS.srgb_luminance(out)[region]))
    print('SHADED body texels', int(region.sum()), 'native pixels', n, 'profile', np.round(curve[::5], 3).tolist(),
          'median luminance', round(before, 3), '->', round(after, 3))


if __name__ == '__main__':
    main()
