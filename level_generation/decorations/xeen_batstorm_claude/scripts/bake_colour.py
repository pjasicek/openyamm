#!/usr/bin/env python3
"""Bat storm: bake the Xeen bat's LOD0 base colour through the xbat_a ramps (the engine's region-ramp maths, via
claude_shared/tier_textures.apply) into one plain colour texture, and keep its normal map (both 512).
Usage: bake_colour.py <xeen_bat.glb> <out dir>"""
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'creatures/claude_shared'))
from tier_textures import apply  # noqa: E402


def read(path):
    raw = Path(path).read_bytes()
    n = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + n])
    rest = raw[20 + n:]
    blen = struct.unpack_from('<I', rest, 0)[0]
    return doc, rest[8:8 + blen]


def image(doc, binary, index):
    view = doc['bufferViews'][doc['images'][index]['bufferView']]
    start = view.get('byteOffset', 0)
    return Image.open(io.BytesIO(binary[start:start + view['byteLength']]))


doc, binary = read(sys.argv[1])
out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
material = next(m for m in doc['materials'] if m['name'] == 'Bat_A_xbat_a')
tex = lambda ref: doc['textures'][ref['index']]['source']
base = image(doc, binary, tex(material['pbrMetallicRoughness']['baseColorTexture'])).convert('RGB')
mask = image(doc, binary, tex(material['extras']['openyamm_region_mask'])).convert('RGBA')
normal = image(doc, binary, tex(material['normalTexture'])).convert('RGB')
# Resize each channel on its own: the mask's alpha is 0, and an RGBA resize premultiplies it away.
mask = np.stack([np.asarray(channel.resize(base.size), float) for channel in mask.split()], -1)
colour = apply(np.asarray(base, float) / 255, mask / 255,
               material['extras']['openyamm_region_ramps'])
Image.fromarray((np.clip(colour, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((512, 512), Image.LANCZOS).save(
    out / 'batstorm_basecolor.png')
normal.resize((512, 512), Image.LANCZOS).save(out / 'batstorm_normal.png')
print('BAKED', base.size, normal.size)
