#!/usr/bin/env python3
"""pman tiers as one shared skin: region mask (tunic, R) + per-tier ramps fitted to the approved A/B/C textures.

The compose step recoloured B/C as A * (1 - w) + palette_fit(A) * w (compose_pman.py, palettes 798 -> 799 / 800).
w is recovered from the saved textures, written as the mask, and each tier's ramp is fitted to its texture over the
full-weight texels. Writes textures/pman_region_mask.png and textures/pman_ramps.json (input of
claude_shared/region_variants.py)."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared'))
import compose_pman as compose
import region_variants as R

T = HERE.parent / 'textures'
TIERS = {'b': 799, 'c': 800}


def main():
    base = R.load_srgb(T / 'pman_a_basecolor.png')
    flat = np.c_[base.reshape(-1, 3), np.ones(base.shape[0] * base.shape[1])]
    mapped = [np.clip(flat @ compose.fit_palette(pid), 0, 1).reshape(base.shape) for pid in TIERS.values()]
    tiers = {f'pman_{tier}': R.load_srgb(T / f'pman_{tier}_basecolor.png') for tier in 'abc'}
    weight = ndimage.median_filter(R.recover_weight(base, mapped, [tiers['pman_b'], tiers['pman_c']]), size=3)
    R.write_mask([weight], T / 'pman_region_mask.png')
    # Runtime body base colour is 1K since the head has its own texture set (ramps are fitted at 2K).
    Image.open(T / 'pman_a_basecolor.png').resize((1024, 1024), Image.LANCZOS).save(
        T / 'pman_a_basecolor_1k.png', optimize=True)
    ramps, report = R.fit_ramps(base, tiers, weight)
    config = {'variants': ['pman_a', 'pman_b', 'pman_c'],
              'materials': [{'base': 'Peasant_A', 'prefix': 'Peasant', 'mask': 'pman_region_mask.png',
                             'regions': ['tunic'], 'palettes': {'pman_a': 798, 'pman_b': 799, 'pman_c': 800},
                             'ramps': {variant: [ramp] for variant, ramp in ramps.items()}, 'fit': report}]}
    (T / 'pman_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
    print(json.dumps({'weight_texels': int((weight > 0.5).sum()), 'fit': report}))


if __name__ == '__main__':
    main()
