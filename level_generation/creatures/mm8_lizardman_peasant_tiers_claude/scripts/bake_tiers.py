#!/usr/bin/env python3
"""Review copies of a ramp-recoloured GLB: one file per variant with the shader's region recolour (fs_model.sc: every
mask channel with a ramp) baked into the base colour, LOD/shadow meshes dropped. Usage: bake_tiers.py <glb> <out dir>
[tag] -> <out>/<variant>_<tag>.glb"""
import copy
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
src, out = Path(sys.argv[1]), Path(sys.argv[2]); tag = sys.argv[3] if len(sys.argv) > 3 else 'v'
out.mkdir(parents=True, exist_ok=True)
doc0, bin0 = read_glb(src)


def tex_image(doc, binary, tex):
    v = doc['bufferViews'][doc['images'][doc['textures'][tex]['source']]['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(binary[o:o + v['byteLength']])))


variants = [v['name'] for v in doc0['extensions']['KHR_materials_variants']['variants']]
for k, name in enumerate(variants):
    doc, binary = copy.deepcopy(doc0), bytearray(bin0)
    prim = next(p for m in doc['meshes'] for p in m['primitives'] if 'KHR_materials_variants' in p.get('extensions', {}))
    mat = doc['materials'][next(m['material'] for m in prim['extensions']['KHR_materials_variants']['mappings'] if k in m['variants'])]
    base = tex_image(doc, binary, mat['pbrMetallicRoughness']['baseColorTexture']['index']).convert('RGB')
    mask = np.asarray(tex_image(doc, binary, mat['extras']['openyamm_region_mask']['index']).convert('RGBA').resize(base.size), float) / 255
    c = lin(np.asarray(base, float) / 255); l = c @ [0.2126, 0.7152, 0.0722]
    for ch, ramp in enumerate(mat['extras']['openyamm_region_ramps']):
        lo, hi = ramp['range']; cols = np.array(ramp['colors']); x = np.clip((l - lo) / (hi - lo), 0, 1) * 15
        i = np.minimum(x.astype(int), 14); f = (x - i)[..., None]
        c = c * (1 - mask[..., ch:ch + 1]) + (cols[i] * (1 - f) + cols[i + 1] * f) * mask[..., ch:ch + 1]
    buf = io.BytesIO(); Image.fromarray((np.clip(srgb(c), 0, 1) * 255 + .5).astype(np.uint8)).save(buf, 'PNG')
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())}); binary += buf.getvalue()
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'baked_{name}'})
    doc['textures'].append({'source': len(doc['images']) - 1})
    for m in doc['materials']:
        m['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}; m.pop('extras', None)
    for mesh in doc['meshes']:
        mesh.pop('extras', None)
        for p in mesh['primitives']:
            p.pop('extensions', None)
    for n in doc['nodes']:   # full detail only: drop the LOD and shadow meshes from the scene
        if 'mesh' in n and doc['meshes'][n['mesh']]['name'].endswith('Shadow'):
            n.pop('mesh')
    write_glb(out / f'{name}_{tag}.glb', doc, bytes(binary)); print('BAKED', name)
