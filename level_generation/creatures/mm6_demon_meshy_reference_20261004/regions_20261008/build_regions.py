#!/usr/bin/env python3
"""Demon A/B/C as one shared skin (CLAUDE_CREATURE_TEXTURES.md): A's body textures + region mask + per-tier ramps.

Regions on A's body base colour: R = skin (dark grey), G = harness (green). Cream bone/padding stays unchanged.
Each tier's ramps are fitted to that tier's previous Meshy body texture over the same texels (UVs correspond, see
../variants_20261006/README.md), so B/C keep their overall colours (green skin/olive harness, red skin/harness) and
lose only their separate Meshy paint detail. Irises stay separate variant materials.
Usage: build_regions.py <installed mm6_demon.glb> <out.glb>"""
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared'))
import region_variants as R

BODY = {'demon_a': 'Demon_Meshy_Body', 'demon_b': 'demon_b_Meshy_Body', 'demon_c': 'demon_c_Meshy_Body'}


def body_image(doc, binary, material_name):
    material = next(m for m in doc['materials'] if m['name'] == material_name)
    source = doc['textures'][material['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
    view = doc['bufferViews'][doc['images'][source]['bufferView']]
    start = view.get('byteOffset', 0)
    image = Image.open(io.BytesIO(binary[start:start + view['byteLength']])).convert('RGB')
    return np.asarray(image, dtype=np.float64) / 255.0


def smooth(edge0, edge1, value):
    t = np.clip((value - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)


def main():
    source, destination = Path(sys.argv[1]), Path(sys.argv[2])
    doc, binary = R.read_glb(source)
    tiers = {variant: body_image(doc, binary, name) for variant, name in BODY.items()}
    base = tiers['demon_a']
    high, low = base.max(-1), base.min(-1)
    saturation = (high - low) / np.maximum(high, 1e-6)
    hue = np.degrees(np.arctan2(np.sqrt(3) * (base[..., 1] - base[..., 2]),
                                2 * base[..., 0] - base[..., 1] - base[..., 2])) % 360
    harness = smooth(0.22, 0.32, saturation) * smooth(80, 95, hue) * (1 - smooth(165, 180, hue))
    cream = smooth(0.55, 0.65, high) * (1 - smooth(0.3, 0.4, saturation)) * (1 - harness)
    skin = np.clip(1 - harness - cream, 0, 1)
    harness, skin = (ndimage.gaussian_filter(region, 0.7) for region in (harness, skin))
    R.write_mask([skin, harness], HERE / 'demon_region_mask.png')

    skin_ramps, skin_report = R.fit_ramps(base, tiers, skin)
    harness_ramps, harness_report = R.fit_ramps(base, tiers, harness)
    config = {'variants': list(BODY),
              'materials': [{'base': 'Demon_Meshy_Body', 'prefix': 'Demon_Body', 'mask': 'demon_region_mask.png',
                             'regions': ['skin', 'harness'],
                             'ramps': {variant: [skin_ramps[variant], harness_ramps[variant]] for variant in BODY},
                             'fit': {'skin': skin_report, 'harness': harness_report}}]}
    (HERE / 'demon_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
    print(json.dumps(config['materials'][0]['fit']))
    # Skin without the grey specular sheen (CLAUDE_CREATURE_TEXTURES.md, Specular); claws and irises keep theirs.
    R.apply_variants(source, destination, HERE / 'demon_ramps.json',
                     [('Demon_Body', 'openyamm_specular', 0.0), ('Demon_Body', 'pbr.metallicFactor', 0.0)])


if __name__ == '__main__':
    main()
