#!/usr/bin/env python3
"""Review-viewer GLBs of the Warlock with her wand (adapted from mm8_m460_reduce_claude/scripts/viewer_staff.py):
viewer_variants.py writes review/viewer/mm7_m426_<tier>_<tag>.glb for the source runtime (r100) and the reduction (body,
tier ramps baked); the wand is unchanged, so its skinned primitive (rigid on the `Staff` joint) is copied from the
source project's viewer file mm7_m426_claude/review/viewer/mm7_m426_<tier>.glb into both, joints remapped by name.
Usage: viewer_wand.py <tag> [...]"""
import copy, shutil, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402
HERE = Path(__file__).resolve().parents[1]; V = HERE / 'review/viewer'; INST = HERE.parent / 'mm7_m426_claude/review/viewer'


def copy_texture(doc, binary, sdoc, sbin, tex_index):
    st = sdoc['textures'][tex_index]; im = sdoc['images'][st['source']]; bv = sdoc['bufferViews'][im['bufferView']]
    data = sbin[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': im.get('mimeType', 'image/png'),
                          'name': im.get('name', 'staff')})
    t = {'source': len(doc['images']) - 1}
    if 'sampler' in st:
        doc.setdefault('samplers', []).append(copy.deepcopy(sdoc['samplers'][st['sampler']])); t['sampler'] = len(doc['samplers']) - 1
    doc['textures'].append(t)
    return len(doc['textures']) - 1


for tag in sys.argv[1:]:
    for tier in 'abc':
        sdoc, sbin = read_glb(INST / f'mm7_m426_{tier}.glb')
        path = V / f'mm7_m426_{tier}_{tag}.glb'; doc, binary = read_glb(path); binary = bytearray(binary)
        snode = next(n for n in sdoc['nodes'] if 'mesh' in n and 'skin' in n)
        sprim = next(p for p in sdoc['meshes'][snode['mesh']]['primitives'] if 'Staff' in sdoc['materials'][p['material']]['name'])
        node = next(n for n in doc['nodes'] if n.get('name') == 'M426')
        names = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
        remap = [names.index(sdoc['nodes'][j]['name']) for j in sdoc['skins'][snode['skin']]['joints']]
        mat = copy.deepcopy(sdoc['materials'][sprim['material']]); pbr = mat.get('pbrMetallicRoughness', {})
        for key in ('baseColorTexture', 'metallicRoughnessTexture'):
            if key in pbr:
                pbr[key] = {**pbr[key], 'index': copy_texture(doc, binary, sdoc, sbin, pbr[key]['index'])}
        for key in ('normalTexture', 'occlusionTexture', 'emissiveTexture'):
            if key in mat:
                mat[key] = {**mat[key], 'index': copy_texture(doc, binary, sdoc, sbin, mat[key]['index'])}
        mat.pop('extensions', None); doc['materials'].append(mat)
        attrs = {}
        for sem, idx in sprim['attributes'].items():
            acc = sdoc['accessors'][idx]; packed = accessor_bytes(sdoc, sbin, idx)
            if sem.startswith('JOINTS_'):
                code = {5121: 'B', 5123: 'H'}[acc['componentType']]
                packed = struct.pack('<' + code * (len(packed) // struct.calcsize(code)),
                                     *(remap[v[0]] for v in struct.iter_unpack('<' + code, packed)))
            attrs[sem] = append_accessor(doc, binary, acc, packed)
        ind = append_accessor(doc, binary, sdoc['accessors'][sprim['indices']], accessor_bytes(sdoc, sbin, sprim['indices']))
        doc['meshes'][node['mesh']]['primitives'].append({'attributes': attrs, 'indices': ind, 'material': len(doc['materials']) - 1})
        write_glb(path, doc, bytes(binary))
        print('WAND', tag, tier, 'joints remapped', len(remap))
