#!/usr/bin/env python3
"""Shared-skin tiers from a compose step's region weights (CLAUDE_CREATURE_TEXTURES.md).

Reads <textures>/<prefix>_region_weights.npz (array `names` = region order = mask channels, plus one HxW weight per
name, written by the project's compose script) and the graded A/B/C base colours, fits each region's ramp per tier
(region_variants.fit_ramps), and writes <prefix>_region_mask.png and <prefix>_ramps.json for region_variants.py.
The shared skin is tier A's graded base colour; B/C graded textures are only fitting targets.

Usage: fit_tier_regions.py <textures dir> <prefix> <base material name> <material prefix> [--suffix _graded]"""
import argparse
import json
from pathlib import Path

import numpy as np

import region_variants as R


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('textures', type=Path)
    parser.add_argument('prefix')
    parser.add_argument('base_material')
    parser.add_argument('material_prefix')
    parser.add_argument('--suffix', default='_graded')
    args = parser.parse_args()
    T, prefix = args.textures, args.prefix
    weights = np.load(T / f'{prefix}_region_weights.npz')
    names = [str(name) for name in weights['names']]
    variants = [f'{prefix}_{tier}' for tier in 'abc']
    tiers = {variant: R.load_srgb(T / f'{variant}_basecolor{args.suffix}.png') for variant in variants}
    base = tiers[variants[0]]
    regions = [np.asarray(weights[name], dtype=np.float64) for name in names]
    R.write_mask(regions, T / f'{prefix}_region_mask.png')
    ramps = {variant: [] for variant in variants}
    report = {}
    for name, weight in zip(names, regions):
        fitted, report[name] = R.fit_ramps(base, tiers, weight)
        for variant in variants:
            ramps[variant].append(fitted[variant])
    config = {'variants': variants,
              'materials': [{'base': args.base_material, 'prefix': args.material_prefix,
                             'mask': f'{prefix}_region_mask.png', 'regions': names, 'ramps': ramps,
                             'fit': report}]}
    (T / f'{prefix}_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
