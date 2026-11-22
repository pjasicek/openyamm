#!/usr/bin/env python3
"""The far LOD copies of the glowing skin (Mantis_LAVA_LOD2/LOD3, own UVs from lod_repair's unwrap) inherit LOD0's
emissive texture, which does not fit their UVs. Give each its own grey emission map from its own transferred region
mask: G (ball joints) x 0.55 + B (eyes) x 0.9, about the LOD0 mask's mean on those regions (the crevice and chest-crack
detail of textures/mantis_emission_mask.png is below a far level's resolution). Usage: far_emission.py in.glb out.glb"""
import io, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
from emission import read_glb, write_glb   # noqa: E402
doc, binary = read_glb(sys.argv[1])


def image_bytes(index):
    img = doc['images'][doc['textures'][index]['source']]
    view = doc['bufferViews'][img['bufferView']]
    off = view.get('byteOffset', 0)
    return bytes(binary[off:off + view['byteLength']])


done = {}
for m in doc['materials']:
    if '_LOD' not in m.get('name', '') or 'emissiveTexture' not in m:
        continue
    key = m['extras']['openyamm_region_mask']['index']
    if key not in done:
        mask = np.asarray(Image.open(io.BytesIO(image_bytes(key))).convert('RGBA'), np.float32) / 255
        grey = np.clip(mask[..., 1] * 0.55 + mask[..., 2] * 0.9, 0, 1)
        png = io.BytesIO(); Image.fromarray((grey * 255 + 0.5).astype(np.uint8), 'L').convert('RGB').save(png, 'PNG')
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(png.getvalue())})
        binary += png.getvalue()
        doc['images'].append({'name': m['name'] + '_emission', 'mimeType': 'image/png',
                              'bufferView': len(doc['bufferViews']) - 1})
        tex = {'source': len(doc['images']) - 1}
        if 'sampler' in doc['textures'][m['emissiveTexture']['index']]:
            tex['sampler'] = doc['textures'][m['emissiveTexture']['index']]['sampler']
        doc['textures'].append(tex)
        done[key] = len(doc['textures']) - 1
        print('FAR_EMISSION', m['name'], grey.shape, round(float(grey.mean()), 4))
    m['emissiveTexture'] = {'index': done[key]}
doc['buffers'][0]['byteLength'] = len(binary)
write_glb(sys.argv[2], doc, binary)
