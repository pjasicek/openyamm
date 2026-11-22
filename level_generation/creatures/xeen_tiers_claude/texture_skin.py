#!/usr/bin/env python3
"""Add Xeen skins to a model whose skins are separate base-colour textures (no region mask): each new skin copies the
materials of an existing skin and points them at recoloured copies of their base-colour images (lane S, D-57: the
Xeen mummy copy). Recolour: every texel becomes the target colour scaled by its luminance relative to the image's mean
luminance (raised to `contrast`), so the shading and the wrapping pattern survive.

    texture_skin.py <in.glb> <out.glb> <spec.json>
spec: {"variants": {"<new skin>": {"from": "<skin>", "mid": "#rrggbb", "contrast": 1.0}}}
"""
import copy
import io
import json
import sys

import numpy as np
from PIL import Image

from xeen_tiers import read, write


def image_bytes(doc, binary, index):
    view = doc['bufferViews'][doc['images'][index]['bufferView']]
    start = view.get('byteOffset', 0)
    return binary[start:start + view['byteLength']]


def append_image(doc, binary, data, mime):
    binary = binary + b'\0' * ((-len(binary)) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary = binary + data
    doc['buffers'][0]['byteLength'] = len(binary)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': mime})
    return binary, len(doc['images']) - 1


def recolour(data, mid, contrast):
    im = Image.open(io.BytesIO(data))
    mode = im.mode
    rgba = np.asarray(im.convert('RGBA')).astype(np.float32) / 255.0
    lin = np.where(rgba[..., :3] <= 0.04045, rgba[..., :3] / 12.92, ((rgba[..., :3] + 0.055) / 1.055) ** 2.4)
    lum = lin @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    ratio = (lum / max(float(lum.mean()), 1e-4)) ** contrast
    target = np.array([int(mid[i:i + 2], 16) / 255.0 for i in (1, 3, 5)], dtype=np.float32)
    target = np.where(target <= 0.04045, target / 12.92, ((target + 0.055) / 1.055) ** 2.4)
    out = np.clip(ratio[..., None] * target, 0.0, 1.0)
    srgb = np.where(out <= 0.0031308, out * 12.92, 1.055 * out ** (1 / 2.4) - 0.055)
    rgba[..., :3] = srgb
    result = Image.fromarray((rgba * 255.0 + 0.5).astype(np.uint8), 'RGBA')
    if 'A' not in mode:
        result = result.convert('RGB')
    buf = io.BytesIO()
    result.save(buf, 'PNG')
    return buf.getvalue()


def main(src, dst, spec_path):
    doc, binary = read(src)
    spec = json.load(open(spec_path))['variants']
    variants = doc['extensions']['KHR_materials_variants']['variants']
    names = [v['name'] for v in variants]
    for new, rule in spec.items():
        if new in names:
            raise SystemExit(f'{new} exists')
        source_index = names.index(rule['from'])
        variants.append({'name': new})
        names.append(new)
        new_index = len(variants) - 1
        copied = {}
        for mesh in doc['meshes']:
            for prim in mesh['primitives']:
                maps = prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])
                for m in list(maps):
                    if source_index not in m['variants']:
                        continue
                    old = m['material']
                    if old not in copied:
                        mat = copy.deepcopy(doc['materials'][old])
                        mat['name'] = mat.get('name', 'mat') + '_' + new
                        tex = mat.get('pbrMetallicRoughness', {}).get('baseColorTexture')
                        if tex is not None:
                            image = doc['textures'][tex['index']]['source']
                            data = recolour(image_bytes(doc, binary, image), rule['mid'], rule.get('contrast', 1.0))
                            binary, new_image = append_image(doc, binary, data, 'image/png')
                            new_texture = copy.deepcopy(doc['textures'][tex['index']])
                            new_texture['source'] = new_image
                            doc['textures'].append(new_texture)
                            tex['index'] = len(doc['textures']) - 1
                        doc['materials'].append(mat)
                        copied[old] = len(doc['materials']) - 1
                    maps.append({'material': copied[old], 'variants': [new_index]})
        print('VARIANT', new, 'from', rule['from'], 'materials', len(copied))
    write(dst, doc, binary)
    print('WROTE', dst)


if __name__ == '__main__':
    main(*sys.argv[1:4])
