#!/usr/bin/env python3
"""FD-04's lizard, stage 1: bake the Thunder Lizard's region ramps into plain base colours (a decoration has no tiers;
claude_shared/tier_textures.py is the shader's maths). For each texture set (LOD0/1, LOD2, LOD3) and each skin letter
writes work/tex/set<k>_<letter>_basecolor.png, and the set's normal and metallic-roughness maps.
Usage: textures.py"""
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'level_generation' / 'creatures' / 'claude_shared'))
from tier_textures import apply  # noqa: E402

SOURCE = REPO / 'assets_source/worlds/mm8/models/mm8_m516.glb'
out = PROJECT / 'work' / 'tex'
out.mkdir(parents=True, exist_ok=True)
raw = SOURCE.read_bytes()
size = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + size])
binary = raw[28 + size:]


def image(index):
    tex = doc['textures'][index]
    view = doc['bufferViews'][doc['images'][tex['source']]['bufferView']]
    data = binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]
    return Image.open(io.BytesIO(data))


materials = {m['name']: m for m in doc['materials']}
for key, suffix in (('0', ''), ('2', '_LOD2'), ('3', '_LOD3')):
    for letter in 'ABC':
        mat = materials[f'ThunderLizard_{letter}{suffix}']
        pbr = mat['pbrMetallicRoughness']
        base = np.asarray(image(pbr['baseColorTexture']['index']).convert('RGB')).astype(np.float64) / 255
        bands = image(mat['extras']['openyamm_region_mask']['index']).convert('RGBA').split()
        dims = (base.shape[1], base.shape[0])
        mask = np.stack([np.asarray(b if b.size == dims else b.resize(dims, Image.BILINEAR), np.float64) / 255
                         for b in bands], -1)
        colour = apply(base, mask, mat['extras']['openyamm_region_ramps'])
        Image.fromarray((np.clip(colour, 0, 1) * 255 + 0.5).astype(np.uint8)).save(
            out / f'set{key}_{letter}_basecolor.png', optimize=True)
        if letter == 'A':
            image(mat['normalTexture']['index']).convert('RGB').save(out / f'set{key}_normal.png', optimize=True)
            image(pbr['metallicRoughnessTexture']['index']).convert('RGB').save(out / f'set{key}_mr.png',
                                                                                 optimize=True)
        print('SET', key, letter, dims, 'extras', sorted(mat.get('extras', {})))
