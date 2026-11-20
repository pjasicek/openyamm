#!/usr/bin/env python3
"""Add tier B/C materials from the material-only exports as KHR_materials_variants (wdm_a/b/c).
Every material named Flying_A_<part> in the runtime GLB gets Flying_B_<part>/Flying_C_<part> from the tier exports,
with their textures appended (deduplicated by content); untiered materials map to themselves.
Usage: merge_variants.py runtime.glb tier_b.glb tier_c.glb out.glb"""
import copy, hashlib, json, struct, sys
from pathlib import Path


def read_glb(path):
    raw = Path(path).read_bytes()
    n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write_glb(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4)
    doc['buffers'][0]['byteLength'] = len(binary)
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    Path(path).write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                           + struct.pack('<II', len(enc), 0x4e4f534a) + enc
                           + struct.pack('<II', len(binary), 0x004e4942) + binary)


def image_bytes(doc, binary, index):
    view = doc['bufferViews'][doc['images'][index]['bufferView']]
    start = view.get('byteOffset', 0)
    return bytes(binary[start:start + view['byteLength']]), doc['images'][index].get('mimeType', 'image/png')


def main():
    doc, binary = read_glb(sys.argv[1])
    known = {}
    for i in range(len(doc['images'])):
        known[hashlib.sha1(image_bytes(doc, binary, i)[0]).hexdigest()] = i
    sampler = 0 if doc.get('samplers') else None

    def import_texture(src_doc, src_bin, tex_index):
        data, mime = image_bytes(src_doc, src_bin, src_doc['textures'][tex_index]['source'])
        key = hashlib.sha1(data).hexdigest()
        if key not in known:
            binary.extend(b'\0' * (-len(binary) % 4))
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
            binary.extend(data)
            doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': mime})
            known[key] = len(doc['images']) - 1
        texture = {'source': known[key]}
        if sampler is not None:
            texture['sampler'] = sampler
        for i, t in enumerate(doc['textures']):
            if t == texture:
                return i
        doc['textures'].append(texture)
        return len(doc['textures']) - 1

    tiers = {'b': read_glb(sys.argv[2]), 'c': read_glb(sys.argv[3])}
    variant_of = {}
    for mi, mat in enumerate(list(doc['materials'])):
        name = mat.get('name', '')
        variant_of[mi] = {'a': mi}
        if not name.startswith('Flying_A_'):
            variant_of[mi].update(b=mi, c=mi)
            continue
        for t, (tdoc, tbin) in tiers.items():
            want = name.replace('Flying_A_', f'Flying_{t.upper()}_')
            src = next(m for m in tdoc['materials'] if m.get('name') == want)
            new = copy.deepcopy(src)
            for holder in (new, new.get('pbrMetallicRoughness', {})):
                for key, info in list(holder.items()):
                    if key.endswith('Texture') and isinstance(info, dict) and 'index' in info:
                        info['index'] = import_texture(tdoc, tbin, info['index'])
            doc['materials'].append(new)
            variant_of[mi][t] = len(doc['materials']) - 1
    doc.setdefault('extensions', {})['KHR_materials_variants'] = {
        'variants': [{'name': 'wdm_a'}, {'name': 'wdm_b'}, {'name': 'wdm_c'}]}
    mapped = 0
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            m = prim.get('material')
            if m is None:
                continue
            prim.setdefault('extensions', {})['KHR_materials_variants'] = {
                'mappings': [{'material': variant_of[m][t], 'variants': [i]} for i, t in enumerate('abc')]}
            mapped += 1
    doc.setdefault('extensionsUsed', [])
    if 'KHR_materials_variants' not in doc['extensionsUsed']:
        doc['extensionsUsed'].append('KHR_materials_variants')
    write_glb(sys.argv[4], doc, binary)
    print(f'{sys.argv[4]}: {len(doc["materials"])} materials, {mapped} primitives mapped, {len(doc["images"])} images')


main()
