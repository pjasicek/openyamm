#!/usr/bin/env python3
"""The far LOD materials (Guardian_A_LOD2/LOD3, own UVs from lod_repair's unwrap) inherit LOD0's emissive texture,
which does not fit their UVs. Give each its own emission map, built from its own transferred region mask:
G (gem) x ruby + B (eye cores) x green, the same colours as textures/guardian_emission_rgb.png at their mean
brightness. Usage: far_emission.py in.glb out.glb"""
import io, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
from emission import read_glb, write_glb   # noqa: E402
RUBY = np.array([0.85, 0.06, 0.04]) * 0.8
GREEN = np.array([0.25, 1.0, 0.25]) * 0.75
doc, binary = read_glb(sys.argv[1])


def image_bytes(index):
    img = doc['images'][doc['textures'][index]['source']]
    view = doc['bufferViews'][img['bufferView']]
    off = view.get('byteOffset', 0)
    return bytes(binary[off:off + view['byteLength']])


for m in doc['materials']:
    if '_LOD' not in m.get('name', '') or 'emissiveTexture' not in m:
        continue
    mask = np.asarray(Image.open(io.BytesIO(image_bytes(m['extras']['openyamm_region_mask']['index']))).convert('RGBA'),
                      np.float32) / 255
    rgb = mask[..., 1:2] * RUBY + mask[..., 2:3] * GREEN
    png = io.BytesIO(); Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(png, 'PNG')
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(png.getvalue())})
    binary += png.getvalue(); doc['buffers'][0]['byteLength'] = len(binary)
    doc['images'].append({'name': m['name'] + '_emission', 'mimeType': 'image/png',
                          'bufferView': len(doc['bufferViews']) - 1})
    base = m['pbrMetallicRoughness']['baseColorTexture']['index']
    tex = {'source': len(doc['images']) - 1}
    if 'sampler' in doc['textures'][base]:
        tex['sampler'] = doc['textures'][base]['sampler']
    doc['textures'].append(tex)
    m['emissiveTexture'] = {'index': len(doc['textures']) - 1}
    print('FAR EMISSION', m['name'], mask.shape[:2], 'glow texels', int((rgb.max(-1) > 0.05).sum()))
write_glb(sys.argv[2], doc, binary)
