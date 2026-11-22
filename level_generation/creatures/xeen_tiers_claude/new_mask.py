#!/usr/bin/env python3
"""Give a model without skins (one plain material per LOD, no region mask) Xeen tier skins that add_region.py can
colour (lane S, session 12: the MM7 treant for the swamp things). Each new skin's materials copy the primitive's own
material and add an empty RGBA region mask (one per LOD atlas, shared by every skin) with no ramps yet; the default
materials stay untouched, so a binding without `skin` still shows the source look.

    new_mask.py <in.glb> <out.glb> <skin> [<skin> ...]

Run add_region.py on the result once per channel (from channel 0); the loader rejects a mask without ramps, so the
intermediate file is not installable.
"""
import copy
import io
import sys

from PIL import Image

import xeen_tiers as xt
from add_region import image_bytes


def append_png(doc, binary, image):
    buf = io.BytesIO()
    image.save(buf, 'PNG', optimize=True)
    data = buf.getvalue()
    binary = binary + b'\0' * ((-len(binary)) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary = binary + data
    doc['buffers'][0]['byteLength'] = len(binary)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png'})
    return binary, len(doc['images']) - 1


def main(src, dst, skins):
    doc, binary = xt.read(src)
    ext = doc.setdefault('extensions', {}).setdefault('KHR_materials_variants', {'variants': []})
    names = [v['name'] for v in ext['variants']]
    for s in skins:
        if s in names:
            raise SystemExit(f'variant {s} exists')
    used = doc.setdefault('extensionsUsed', [])
    if 'KHR_materials_variants' not in used:
        used.append('KHR_materials_variants')
    masks = {}     # base colour texture -> mask texture
    copies = {}    # (material, skin) -> new material
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            mi = prim.get('material')
            if mi is None:
                continue
            mat = doc['materials'][mi]
            base_tex = mat.get('pbrMetallicRoughness', {}).get('baseColorTexture', {}).get('index')
            if base_tex is None:
                continue
            if base_tex not in masks:
                source = doc['textures'][base_tex]['source']
                w, h = Image.open(io.BytesIO(image_bytes(doc, binary, source))).size
                size = (min(w, 1024), min(h, 1024))
                binary, image = append_png(doc, binary, Image.new('RGBA', size, (0, 0, 0, 0)))
                tex = {'source': image}
                if 'sampler' in doc['textures'][base_tex]:
                    tex['sampler'] = doc['textures'][base_tex]['sampler']
                doc['textures'].append(tex)
                masks[base_tex] = len(doc['textures']) - 1
                print(f'mask texture {masks[base_tex]} {size} for base texture {base_tex}')
            maps = prim.setdefault('extensions', {}).setdefault('KHR_materials_variants', {'mappings': []})['mappings']
            for s in skins:
                if (mi, s) not in copies:
                    new = copy.deepcopy(mat)
                    new['name'] = mat.get('name', 'mat') + '_' + s
                    extras = new.setdefault('extras', {})
                    extras['openyamm_region_mask'] = {'index': masks[base_tex]}
                    extras['openyamm_region_ramps'] = []
                    doc['materials'].append(new)
                    copies[(mi, s)] = len(doc['materials']) - 1
                maps.append({'material': copies[(mi, s)], 'variants': [len(names) + skins.index(s)]})
    for s in skins:
        ext['variants'].append({'name': s})
    xt.write(dst, doc, binary)
    print('WROTE', dst, 'skins', skins, 'materials added', len(copies))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
