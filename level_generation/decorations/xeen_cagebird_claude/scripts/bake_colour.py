#!/usr/bin/env python3
"""Stage 1: the cage bird's colour. A decoration has no tier skins, so each of the crow's six texture sets (body and
head at LOD0/1, LOD2, LOD3) gets one skin's region ramps baked into its base colour (claude_shared/tier_textures.py
apply(), the shader's maths), then the plumage is recoloured by a gradient map: the baked plumage's lightness, ranked
between its 2nd and 98th percentiles, picks a colour from the palette's plumage stops (so the feather detail stays and
the bird turns from the dark eagle into a bright cage bird). Beak, eyes and legs keep the skin's colours unless the
palette names stops for them. Normal and metal/roughness maps are copied unchanged.

Usage: bake_colour.py [palette]   (palettes in cagebird.json; default its `palette`)
Writes work/tex/<set>_basecolor.png, <set>_normal.png, <set>_mr.png for set in body0 head0 body2 head2 body3 head3."""
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / 'creatures' / 'claude_shared'))
from cagelib import PROJECT, Model  # noqa: E402
from tier_textures import apply  # noqa: E402

CFG = json.loads((HERE / 'cagebird.json').read_text())
SETS = {'body0': '{skin}', 'head0': 'CrowHead_{tag}', 'body2': '{skin}_LOD2', 'head2': 'CrowHead_{tag}_LOD2',
        'body3': '{skin}_LOD3', 'head3': 'CrowHead_{tag}_LOD3'}
# region channel of each set's mask: body R plumage, A legs; head R plumage, G beak, B eyes
REGIONS = {'body': {'plumage': 0, 'legs': 3}, 'head': {'plumage': 0, 'beak': 1, 'eyes': 2}}
LUMA = np.array([0.2126, 0.7152, 0.0722])


def gradient(stops, t):
    """sRGB 0..1 colours along stops [[t, [r, g, b] 0..255], ...] at t (any shape)."""
    ts = np.array([s[0] for s in stops], float)
    cs = np.array([s[1] for s in stops], float) / 255
    return np.stack([np.interp(t, ts, cs[:, c]) for c in range(3)], -1)


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else CFG['palette']
    palette = CFG['palettes'][name]
    skin = palette['skin']
    tag = skin.split('_')[1]
    model = Model()
    doc, binary = model.doc, model.bin
    materials = {m['name']: m for m in doc['materials']}

    def image(texture):
        view = doc['bufferViews'][doc['images'][doc['textures'][texture]['source']]['bufferView']]
        start = view.get('byteOffset', 0)
        return Image.open(io.BytesIO(bytes(binary[start:start + view['byteLength']])))

    out = PROJECT / 'work' / 'tex'
    out.mkdir(parents=True, exist_ok=True)
    # The plumage's lightness percentiles from the LOD0 sets, shared by the smaller sets so all LODs agree.
    ranks = {}
    for key, pattern in SETS.items():
        kind = key[:4]
        material = materials[pattern.format(skin=skin, tag=tag)]
        pbr = material['pbrMetallicRoughness']
        base_image = image(pbr['baseColorTexture']['index']).convert('RGB')
        base = np.asarray(base_image, np.float64) / 255
        # The mask's alpha is a region (legs), not opacity: resize channel by channel (an RGBA resize premultiplies).
        mask_image = image(material['extras']['openyamm_region_mask']['index']).convert('RGBA')
        mask = np.stack([np.asarray(c.resize(base_image.size, Image.BILINEAR), np.float64) / 255
                         for c in mask_image.split()], -1)
        colour = apply(base, mask, material['extras']['openyamm_region_ramps'])
        lum = colour @ LUMA
        for region, channel in REGIONS[kind].items():
            stops = palette.get(f'{kind}_{region}') or palette.get(region)
            if not stops:
                continue
            weight = mask[..., channel]
            if (kind, region) not in ranks:
                inside = lum[weight > 0.9]
                ranks[(kind, region)] = np.percentile(inside, [2, 98])
            lo, hi = ranks[(kind, region)]
            t = np.clip((lum - lo) / max(hi - lo, 1e-4), 0, 1) ** palette.get('gamma', 1.0)
            target = gradient(stops, t)
            w = (weight * palette.get('strength', 1.0))[..., None]
            colour = colour * (1 - w) + target * w
        Image.fromarray((np.clip(colour, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(
            out / f'{key}_basecolor.png', optimize=True)
        image(material['normalTexture']['index']).convert('RGB').save(out / f'{key}_normal.png', optimize=True)
        image(pbr['metallicRoughnessTexture']['index']).convert('RGB').save(out / f'{key}_mr.png', optimize=True)
        print(f'{key}: {material["name"]} {base_image.size[0]}x{base_image.size[1]}')
    print('palette', name)


if __name__ == '__main__':
    main()
