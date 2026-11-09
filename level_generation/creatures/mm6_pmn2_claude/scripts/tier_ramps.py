#!/usr/bin/env python3
"""Mage tiers as one shared skin: region mask (robe, R) + per-tier ramps.

Migrates the former single tint (textures/tints.json, colour = luminance * tint inside the robe mask that
prepare_textures.py writes into the metallic-roughness red channel) to the region format: the mask is copied to its
own image and each tier's ramp is luminance * tint over the robe's luminance range, so the look is unchanged.
Since 2026-10-08 the robe ramps come from native shading transfer instead of the tint (claude_shared/native_shading.py,
../NATIVE_SHADING_TRANSFER.md): colour by brightness through the same native cloth pixels in each palette
(work/native_shading/pixels.npz), times GAIN, saturation x CHROMA. The tint version is in textures_pre_native/.
Writes textures/pmn2_region_mask.png and textures/pmn2_ramps.json (input of claude_shared/region_variants.py)."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared'))
import region_variants as R
import native_shading as NS

T = HERE.parent / 'textures'
PALETTES = {'pmn2_a': 801, 'pmn2_b': 802, 'pmn2_c': 803}
GAIN = 1.0
CHROMA = 1.1
# Boss tier (actors.yml "Necromancer A"): no native palette, a dark violet robe over the same luminance range, from
# near-black folds to a muted amethyst on the lit cloth (linear RGB at the darkest and brightest stop).
BOSS_TIER = 'pmn2_d'
BOSS_DARK = (0.006, 0.001, 0.012)
BOSS_LIGHT = (0.21, 0.035, 0.36)


def boss_ramp(reference):
    stops = np.linspace(0.0, 1.0, 16) ** 1.35
    colors = [[round(float(d + (l - d) * t), 6) for d, l in zip(BOSS_DARK, BOSS_LIGHT)] for t in stops]
    return [{'range': reference[0]['range'], 'colors': colors}]


def main():
    base = R.load_srgb(T / 'pmn2_a_basecolor.png')
    mask_image = Image.open(T / 'pmn2_metal_rough_1k.png').convert('RGB').getchannel('R')
    mask_full = np.asarray(mask_image.resize(base.shape[1::-1], Image.BILINEAR), dtype=np.float64) / 255.0
    R.write_mask([np.asarray(mask_image, dtype=np.float64) / 255.0], T / 'pmn2_region_mask.png',
                 size=mask_image.size[0])
    # Runtime body base colour is 1K since the head has its own texture set.
    Image.open(T / 'pmn2_a_basecolor.png').resize((1024, 1024), Image.LANCZOS).save(
        T / 'pmn2_a_basecolor_1k.png', optimize=True)
    pixels = np.load(HERE.parent / 'work' / 'native_shading' / 'pixels.npz')
    ramps = NS.transfer_ramps(base, {'robe': mask_full}, pixels, {'robe': 'robe'}, PALETTES, reference=801,
                              gain={'robe': GAIN}, chroma=CHROMA)
    ramps[BOSS_TIER] = boss_ramp(ramps['pmn2_a'])
    config = {'variants': ['pmn2_a', 'pmn2_b', 'pmn2_c', BOSS_TIER],
              'materials': [{'base': 'Mage_A', 'prefix': 'Mage', 'mask': 'pmn2_region_mask.png',
                             'regions': ['robe'], 'palettes': PALETTES,
                             'ramps': ramps}]}
    (T / 'pmn2_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
    print(json.dumps({'mask_texels': int((mask_full > 0.5).sum()), 'ranges': {k: v[0]['range'] for k, v in ramps.items()}}))


if __name__ == '__main__':
    main()
