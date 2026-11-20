#!/usr/bin/env python3
"""Patrol Unit tiers as one shared skin: ramps per region from the native palette sprites
(CLAUDE_CREATURE_TEXTURES.md). BRobot A/B/C = palettes 810 steel / 811 blue / 812 copper.

Caps, rings and belt: native shading transfer (claude_shared/native_shading.py, ../NATIVE_SHADING_TRANSFER.md). The
shared base carries the native tier-A brightness by elevation (compose_rob1.py), so the ramps transfer colour by
brightness through the same native pixels (work/native_shading/pixels.npz: side, rear three-quarter and back views,
regions by elevation), read in each tier's palette, times GAIN (the sprites' shading is in the base already; the gain
only offsets the engine's own darkening) and saturation x CHROMA.
Eye: the restored mask's A channel (death frames skipped, where A holds the explosion), luminance quantile mapping.
Also writes the baked AO into the red channel of the metal/roughness map (glTF ORM packing).
Writes textures/rob1_region_mask.png, textures/rob1_ramps.json."""
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
SPRITES = ROOT.parent / 'mm6_rob1'
PALETTES = {'rob1_a': 810, 'rob1_b': 811, 'rob1_c': 812}
REGIONS = ['caps', 'rings', 'belt', 'eye']          # mask channels R, G, B, A
NATIVE_REGION = {'caps': 'caps', 'rings': 'rings', 'belt': 'belt'}   # mask region -> native_shading.json region
GAIN = {'caps': 1.1, 'rings': 1.0, 'belt': 1.1, 'eye': 1.0}
CHROMA = 1.25                                       # saturation boost: the sprites read saturated, ours pastel


def eye_pixels(palette):
    pixels = []
    for mask_path in sorted((SPRITES / 'masks_2x').glob('rob1*.png')):
        name = mask_path.stem
        frame_path = SPRITES / 'native_variants' / f'{name}_{palette}.png'
        if name[4:6] == 'de' or not frame_path.exists():
            continue
        mask = np.asarray(Image.open(mask_path).convert('RGBA'), np.float64)[..., 3] / 255
        mask = mask.reshape(mask.shape[0] // 2, 2, mask.shape[1] // 2, 2).mean((1, 3))
        frame = np.asarray(Image.open(frame_path).convert('RGBA'), np.float64) / 255
        pixels.append(frame[..., :3][(mask > 0.75) & (frame[..., 3] > 0.5)])
    pixels = np.concatenate(pixels)
    return pixels[np.argsort(R.srgb_to_linear(pixels) @ R.LUMA)]


def main():
    base = R.load_srgb(T / 'rob1_a_basecolor_graded.png')
    data = np.load(T / 'rob1_region_weights.npz')
    weights = [np.asarray(data[name], np.float64) for name in REGIONS]
    R.write_mask(weights, T / 'rob1_region_mask.png')
    pixels = np.load(ROOT / 'work' / 'native_shading' / 'pixels.npz')
    body = {name: weight for name, weight in zip(REGIONS, weights) if name in NATIVE_REGION}
    ramps = NS.transfer_ramps(base, body, pixels, NATIVE_REGION, PALETTES, reference=810, gain=GAIN, chroma=CHROMA)
    report = {}
    # Eye: luminance quantiles of the restored mask's eye pixels (not in the elevation sample: front views only).
    lum_all = R.luminance(base)
    eye = weights[REGIONS.index('eye')]
    lum = lum_all[eye > 0.9]
    lo, hi = np.percentile(lum, 0.5), np.percentile(lum, 99.5)
    stops = lo + (hi - lo) * np.arange(16) / 15
    quantiles = np.searchsorted(np.sort(lum), stops) / len(lum)
    for variant, palette in PALETTES.items():
        native = eye_pixels(palette)
        colours = []
        for q in quantiles:
            centre = int(np.clip(q, 0, 1) * (len(native) - 1)); half = max(len(native) // 200, 2)
            window = native[max(centre - half, 0):centre + half + 1]
            colours.append(R.srgb_to_linear(np.clip(np.median(window, 0) * GAIN['eye'], 0, 1)))
        ramps[variant].insert(REGIONS.index('eye'), {'range': [round(float(lo), 6), round(float(hi), 6)],
                                                     'colors': np.round(np.clip(colours, 0, 1), 6).tolist()})
        report[variant] = {'eye_pixels': int(len(native))}
    shared = {'mask': 'rob1_region_mask.png', 'regions': REGIONS, 'palettes': PALETTES, 'ramps': ramps}
    config = {'variants': list(PALETTES),
              'materials': [dict(shared, base='Robot_A', prefix='Robot', native=report),
                            dict(shared, base='Robot_Eye', prefix='RobotEye')]}
    (T / 'rob1_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
    ao = Image.open(T / 'rob1_ao_2k.png').convert('L').resize((1024, 1024), Image.LANCZOS)
    mr = Image.open(T / 'rob1_metal_rough_1k.png').convert('RGB')
    Image.merge('RGB', (ao, mr.getchannel('G'), mr.getchannel('B'))).save(T / 'rob1_metal_rough_1k.png')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
