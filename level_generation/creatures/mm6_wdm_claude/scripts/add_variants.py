#!/usr/bin/env python3
"""Colour variants wdm_a/b/c (native palettes 684 purple / 685 olive / 683 dark red) as KHR_materials_variants. Each skin
material (body 'Demon', grafted head 'DemonHead') is copied per tier; copies share every image and differ only in
extras.openyamm_region_ramps (textures/wdm_ramps.json). extras.openyamm_region_mask points at the material's region
mask texture (skin in R), embedded once with a linear sampler.
Usage: add_variants.py in.glb out.glb"""
import copy, json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_glb(path):
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write_glb(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4)
    doc['buffers'][0]['byteLength'] = len(binary)
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                     + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    doc, binary = read_glb(src)
    ramps = json.load(open(ROOT / 'textures' / 'wdm_ramps.json'))
    names = ['wdm_a', 'wdm_b', 'wdm_c']
    # Region masks are linear data: own sampler (bilinear + mips), one image per material, shared by its tiers.
    doc.setdefault('samplers', []).append({'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497})
    sampler = len(doc['samplers']) - 1
    mask_texture = {}
    for material_name, material_ramps in ramps['materials'].items():
        data = (ROOT / 'textures' / material_ramps['mask']).read_bytes()
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
        binary += data
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png',
                              'name': material_ramps['mask'][:-4]})
        doc['textures'].append({'sampler': sampler, 'source': len(doc['images']) - 1})
        mask_texture[material_name] = len(doc['textures']) - 1
    # every skin material (body 'Demon', grafted head 'DemonHead') gets per-tier copies that differ only in ramps
    bases = [i for i, m in enumerate(doc['materials']) if m['name'].split('.')[0] in ('Demon', 'DemonHead')]
    index = {}
    for base in bases:
        stem = doc['materials'][base]['name'].split('.')[0]
        for tier in 'abc':
            if tier == 'a':
                material = doc['materials'][base]; index[(base, 'a')] = base
            else:
                material = copy.deepcopy(doc['materials'][base]); doc['materials'].append(material)
                index[(base, tier)] = len(doc['materials']) - 1
            material['name'] = f'{stem}_{tier.upper()}'
            extras = material.setdefault('extras', {})
            extras.pop('openyamm_tint', None)
            # Organic skin: no specular. Meshy's roughness (0.5-0.7) laid a grey, steel-like sheen over skin and
            # membrane, worst at silhouettes (user review 2026-10-08).
            extras['openyamm_specular'] = 0.0
            # With specular off a metallic texel has no diffuse term and renders black; the compose writes metallic 0,
            # and the factor makes that explicit.
            material.setdefault('pbrMetallicRoughness', {})['metallicFactor'] = 0.0
            extras['openyamm_region_mask'] = {'index': mask_texture[stem]}
            extras['openyamm_region_ramps'] = [{'range': ramps['materials'][stem]['range'],
                                                'colors': ramps['tiers'][tier]['colors']}]
    mapped = 0
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            m = primitive.get('material')
            if m not in bases:
                raise ValueError(f'unexpected primitive material {m}')
            targets = [index[(m, t)] for t in 'abc']
            primitive.setdefault('extensions', {})['KHR_materials_variants'] = {
                'mappings': [{'material': t, 'variants': [i]} for i, t in enumerate(targets)]}
            mapped += 1
    doc.setdefault('extensionsUsed', [])
    if 'KHR_materials_variants' not in doc['extensionsUsed']:
        doc['extensionsUsed'].append('KHR_materials_variants')
    doc.setdefault('extensions', {})['KHR_materials_variants'] = {'variants': [{'name': n} for n in names]}
    write_glb(dst, doc, binary)
    print('VARIANTS', names, 'primitives', mapped, 'region masks', mask_texture)


if __name__ == '__main__':
    main()
