#!/usr/bin/env python3
"""Recolour a model's unmasked materials (fire elemental flames) for chosen skins (lane S, Xeen tiers): for each listed
skin, every primitive whose default material is one of the listed materials gets a copy of that material, mapped to
the skin through KHR_materials_variants, with a region mask that covers it whole and one ramp: the given colour stops
over the texture's own luminance range. Every other skin keeps the default material (no ramp), so it looks as before.

    flame_ramps.py <in.glb> <out.glb> <spec.json>

spec.json:
  {"mask_from": "<material name>",              # a material whose region mask is constant full channel R (reused)
   "percentiles": [2, 98],                     # luminance range of each texture's visible texels (alpha > 0.1)
   "skins": {"<skin>": {"materials": ["<name>", ...], "stops": ["#rrggbb", ...]}}}   # sRGB, dark to bright, 2..16
The stops are resampled evenly to the ramp's 16 entries (linear RGB). Run after xeen_tiers.py made the skin."""
import copy
import json
import sys

import numpy as np

sys.path.insert(0, __import__('os').path.dirname(__file__))
import xeen_tiers as xt  # noqa: E402


def ramp_colors(stops):
    cols = np.array([xt.srgb_hex_to_linear(s) for s in stops])
    x = np.linspace(0, len(cols) - 1, 16)
    return [[round(float(np.interp(xi, np.arange(len(cols)), cols[:, c])), 6) for c in range(3)] for xi in x]


def main(src, dst, spec_path):
    doc, binary = xt.read(src)
    spec = json.load(open(spec_path))
    names = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']]
    by_name = {m['name']: i for i, m in enumerate(doc['materials'])}
    mask = doc['materials'][by_name[spec['mask_from']]]['extras']['openyamm_region_mask']
    lo_p, hi_p = spec.get('percentiles', [2, 98])
    ranges = {}
    for skin, rule in spec['skins'].items():
        if skin.startswith('_'):
            continue
        vi = names.index(skin)
        cloned = {}
        for name in rule['materials']:
            mi = by_name[name]
            if mi not in ranges:
                pbr = doc['materials'][mi]['pbrMetallicRoughness']
                img = np.asarray(xt.texture_image(doc, binary, pbr['baseColorTexture']['index']).convert('RGBA'),
                                 np.float64) / 255
                lum = xt.srgb_to_linear(img[..., :3]) @ np.array([0.2126, 0.7152, 0.0722])
                lum = lum[img[..., 3] > 0.1]
                ranges[mi] = [round(float(np.percentile(lum, lo_p)), 5), round(float(np.percentile(lum, hi_p)), 5)]
            mat = copy.deepcopy(doc['materials'][mi])
            mat['name'] = f'{name}_{skin}'
            ex = mat.setdefault('extras', {})
            ex['openyamm_region_mask'] = copy.deepcopy(mask)
            ex['openyamm_region_ramps'] = [{'range': ranges[mi], 'colors': ramp_colors(rule['stops'])}]
            doc['materials'].append(mat)
            cloned[mi] = len(doc['materials']) - 1
            print(f'{skin}: {name} range {ranges[mi]}')
        for mesh in doc['meshes']:
            for prim in mesh['primitives']:
                if prim.get('material') not in cloned:
                    continue
                maps = prim.setdefault('extensions', {}).setdefault('KHR_materials_variants', {'mappings': []})
                maps['mappings'].append({'material': cloned[prim['material']], 'variants': [vi]})
    xt.write(dst, doc, binary)
    print('WROTE', dst)


if __name__ == '__main__':
    main(*sys.argv[1:4])
