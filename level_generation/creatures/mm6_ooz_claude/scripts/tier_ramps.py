#!/usr/bin/env python3
"""Ooze tiers as one shared skin (CLAUDE_CREATURE_TEXTURES.md): the whole slime is one region (R) recoloured by
per-tier ramps read from the native palettes 780 (green) / 781 (red) / 782 (ochre).

Native pixels aligned across palettes (the same opaque pixels of every native frame in mm6_ooz/native_variants/, all
actions and views, the dark corpse frames excluded) feed claude_shared/native_shading.transfer_ramps: for each ramp
stop (the base texture's slime luminance p0.5..p99.5), the 780 pixels nearest in luminance are read in each palette
(median) x ALBEDO. The near-white highlight pixels are kept (QMAX), so lump tops lifted by compose_ooz.py take
the sprites' pale highlight colours. Writes textures/ooz_region_mask.png (from compose_ooz.py's weight) and
textures/ooz_ramps.json. Usage: tier_ramps.py <base colour png> <slime weight npy>"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import native_shading as NS
import region_variants as R

T = HERE / 'textures'
NV = HERE.parent / 'mm6_ooz' / 'native_variants'
TIERS = {'ooz_a': 780, 'ooz_b': 781, 'ooz_c': 782}
ALBEDO = 0.9                      # in-game A/B with the glossy material: 1.35 read ~1.5x brighter than the sprites
QMAX = 0.995                     # keep the sprites' near-white highlight entries (user: more white-ish)
CHROMA = 1.4                      # in-game A/B: the ochre tier read greyish-beige next to the sprite


def native_pixels():
    cols = {p: [] for p in TIERS.values()}
    for path in sorted(NV.glob('*_780.png')):
        stem = path.name[:-len('_780.png')]
        if stem.startswith('oozdy'):                   # the death splash and corpse are dark residue, not slime
            continue
        imgs = {p: np.asarray(Image.open(NV / f'{stem}_{p}.png').convert('RGBA'), np.float64) / 255
                for p in TIERS.values()}
        mask = imgs[780][..., 3] > 0.9
        for p in TIERS.values():
            cols[p].append(imgs[p][mask][:, :3])
    cols = {p: np.concatenate(v) for p, v in cols.items()}
    lum = NS.srgb_to_linear(cols[780]) @ NS.LUMA
    keep = lum <= np.quantile(lum, QMAX)
    return {'region': np.zeros(int(keep.sum()), int), 'region_names': np.array(['slime']),
            **{f'p{p}': c[keep] for p, c in cols.items()}}


def main():
    base = R.load_srgb(sys.argv[1])
    weight = np.load(sys.argv[2])
    R.write_mask([weight], T / 'ooz_region_mask.png')
    pixels = native_pixels()
    ramps = NS.transfer_ramps(base, {'slime': weight}, pixels, {'slime': 'slime'}, TIERS, reference=780,
                              gain={'slime': ALBEDO}, chroma=CHROMA)
    config = {'variants': list(TIERS),
              'materials': [{'base': 'Ooze_A', 'prefix': 'Ooze', 'mask': 'ooz_region_mask.png', 'regions': ['slime'],
                             'palettes': TIERS, 'ramps': ramps,
                             'native_pixels': int(len(pixels['region']))}]}
    (T / 'ooz_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
    print('RAMPS', {v: ramps[v][0]['range'] for v in ramps}, 'native pixels', len(pixels['region']))


if __name__ == '__main__':
    main()
