#!/usr/bin/env python3
"""Mage tiers as one shared skin: region mask (robe, R) + per-tier ramps.

Migrates the former single tint (textures/tints.json, colour = luminance * tint inside the robe mask that
prepare_textures.py writes into the metallic-roughness red channel) to the region format: the mask is copied to its
own image and each tier's ramp is luminance * tint over the robe's luminance range, so the look is unchanged.
Writes textures/pmn2_region_mask.png and textures/pmn2_ramps.json (input of claude_shared/region_variants.py)."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared'))
import region_variants as R

T = HERE.parent / 'textures'


def main():
    base = R.load_srgb(T / 'pmn2_a_basecolor.png')
    mask_image = Image.open(T / 'pmn2_metal_rough_1k.png').convert('RGB').getchannel('R')
    mask_full = np.asarray(mask_image.resize(base.shape[1::-1], Image.BILINEAR), dtype=np.float64) / 255.0
    R.write_mask([np.asarray(mask_image, dtype=np.float64) / 255.0], T / 'pmn2_region_mask.png',
                 size=mask_image.size[0])
    # Runtime body base colour is 1K since the head has its own texture set.
    Image.open(T / 'pmn2_a_basecolor.png').resize((1024, 1024), Image.LANCZOS).save(
        T / 'pmn2_a_basecolor_1k.png', optimize=True)
    tints = json.loads((T / 'tints.json').read_text())['tints']
    ramps = {f'pmn2_{tier}': [R.tint_ramp(base, mask_full, tints[tier])] for tier in 'abc'}
    config = {'variants': ['pmn2_a', 'pmn2_b', 'pmn2_c'],
              'materials': [{'base': 'Mage_A', 'prefix': 'Mage', 'mask': 'pmn2_region_mask.png',
                             'regions': ['robe'], 'palettes': {'pmn2_a': 801, 'pmn2_b': 802, 'pmn2_c': 803},
                             'ramps': ramps}]}
    (T / 'pmn2_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
    print(json.dumps({'mask_texels': int((mask_full > 0.5).sum()), 'ranges': {k: v[0]['range'] for k, v in ramps.items()}}))


if __name__ == '__main__':
    main()
