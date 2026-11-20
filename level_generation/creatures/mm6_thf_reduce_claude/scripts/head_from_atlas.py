#!/usr/bin/env python3
"""The kept head set (face skin and hair): the head half (x 1056..2080) of each installed merged atlas
(merge_head_material.py: body | 32-px gutter | head) -> textures/thf_head_{basecolor,metal_rough,normal}_1k.png and
thf_head_region_mask.png."""
import io, json, struct
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
raw = (HERE.parents[2] / 'assets_source/worlds/mm6/models/mm6_thf.glb').read_bytes()
n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n]); binary = raw[28 + n:]
names = {'thf_a_basecolor_1k_head_atlas': 'thf_head_basecolor_1k.png', 'thf_metal_rough_1k_head_atlas': 'thf_head_metal_rough_1k.png',
         'thf_normal_1k_head_atlas': 'thf_head_normal_1k.png', 'thf_region_mask_head_atlas': 'thf_head_region_mask.png'}
for im in doc['images']:
    out = names.get(im.get('name'))
    if out is None:
        continue
    v = doc['bufferViews'][im['bufferView']]; s = v.get('byteOffset', 0)
    img = Image.open(io.BytesIO(binary[s:s + v['byteLength']]))
    img.crop((1056, 0, 2080, 1024)).save(HERE / 'textures' / out)
    print('HEAD', out, img.mode)
