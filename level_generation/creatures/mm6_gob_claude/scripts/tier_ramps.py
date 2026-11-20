#!/usr/bin/env python3
"""Goblin tiers as one shared skin: region mask (skin, R) + per-tier ramps fitted to the approved A/B/C textures.

The compose step recoloured B/C as A * (1 - w) + palette_fit(A) * w (compose_gob.py). w is recovered from the saved
textures, written as the mask, and each tier's ramp is fitted to its graded texture over the full-weight texels.
Writes textures/gob_region_mask.png and textures/gob_ramps.json (input of claude_shared/region_variants.py)."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared'))
import compose_gob as G
import region_variants as R

T = HERE.parent / 'textures'
TIERS = {'b': 746, 'c': 747}


def main():
    base = R.load_srgb(T / 'gob_a_basecolor.png')
    skin_select = lambda hh, ss: (hh > 35) & (hh < 120) & (ss > 0.15)
    flat = np.c_[base.reshape(-1, 3), np.ones(base.shape[0] * base.shape[1])]
    mapped = [np.clip(flat @ G.fit_palette(pid, skin_select), 0, 1).reshape(base.shape) for pid in TIERS.values()]
    recoloured = [R.load_srgb(T / f'gob_{tier}_basecolor.png') for tier in TIERS]
    weight = ndimage.median_filter(R.recover_weight(base, mapped, recoloured), size=3)
    R.write_mask([weight], T / 'gob_region_mask.png')
    # Runtime body base colour is 1K since the head has its own texture set (ramps are fitted at 2K).
    Image.open(T / 'gob_a_basecolor_graded.png').resize((1024, 1024), Image.LANCZOS).save(
        T / 'gob_a_basecolor_graded_1k.png', optimize=True)

    graded = {f'gob_{tier}': R.load_srgb(T / f'gob_{tier}_basecolor_graded.png') for tier in 'abc'}
    ramps, report = R.fit_ramps(graded['gob_a'], graded, weight)
    config = {'variants': ['gob_a', 'gob_b', 'gob_c'],
              'materials': [{'base': 'Peasant_A', 'prefix': 'Goblin', 'mask': 'gob_region_mask.png',
                             'regions': ['skin'], 'palettes': {'gob_a': 745, 'gob_b': 746, 'gob_c': 747},
                             'ramps': {variant: [ramp] for variant, ramp in ramps.items()}, 'fit': report}]}
    (T / 'gob_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
    print(json.dumps({'weight_texels': int((weight > 0.5).sum()), 'fit': report}))


if __name__ == '__main__':
    main()
