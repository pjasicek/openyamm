#!/usr/bin/env python3
"""Review-viewer GLBs for the reduction (installed vs reduced): one copy per tier with that tier's materials made primary
(KHR_materials_variants dropped), tier B's base colour replaced by the Guard project's ramp-baked viewer image
(../mm9_guard_claude/work/guard_b_viewer.png, three.js has no region ramps), and the runtime attachments added as children of
their joints the way the game attaches them: the halberd on Xbase (A, B: mm9_guard_halberd; C: mm9_guard_halberd2) and the
helmet plate on Bip01 Head (A: plate_a; B, C: plate_c), LOD0 only, from before/ (unchanged by the reduction).
Usage: viewer_tiers.py <body glb> <prefix> -> review/viewer/<prefix>_{a,b,c}.glb"""
import copy, json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared')); sys.path.insert(0, str(HERE / 'scripts'))
import region_variants as RV  # noqa: E402
import glbpack as G  # noqa: E402
GLB, PREFIX = Path(sys.argv[1]), sys.argv[2]
ATT = {'a': ('mm9_guard_halberd', 'mm9_guard_plate_a'), 'b': ('mm9_guard_halberd', 'mm9_guard_plate_c'),
       'c': ('mm9_guard_halberd2', 'mm9_guard_plate_c')}
JOINT = {'halberd': 'Xbase', 'plate': 'Bip01 Head'}
BVIEW = HERE.parent / 'mm9_guard_claude' / 'work' / 'guard_b_viewer.png'


def add_bytes(doc, binary, data):
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary += data
    return len(doc['bufferViews']) - 1


def attach(doc, binary, path, joint):
    ad, ab = G.read(path); ab = bytes(ab)
    am = ad['meshes'][ad['nodes'][0]['mesh']]; pr = am['primitives'][0]
    att = {}
    for sem, i in pr['attributes'].items():
        a = ad['accessors'][i]
        att[sem] = G.append(doc, binary, a, G.raw_rows(ad, ab, i)); G.set_minmax(doc, binary, att[sem])
    idx = G.append(doc, binary, ad['accessors'][pr['indices']], G.raw_rows(ad, ab, pr['indices']))
    mat = copy.deepcopy(ad['materials'][pr['material']])
    tmap = {}

    def tex(i):
        if i not in tmap:
            src = ad['textures'][i]['source']; im = ad['images'][src]; v = ad['bufferViews'][im['bufferView']]
            o = v.get('byteOffset', 0); bv = add_bytes(doc, binary, ab[o:o + v['byteLength']])
            doc['images'].append({'name': im.get('name', 'att'), 'mimeType': im.get('mimeType', 'image/png'), 'bufferView': bv})
            doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': 0}); tmap[i] = len(doc['textures']) - 1
        return tmap[i]
    pbr = mat.get('pbrMetallicRoughness', {})
    for k in ('baseColorTexture', 'metallicRoughnessTexture'):
        if k in pbr: pbr[k]['index'] = tex(pbr[k]['index'])
    for k in ('normalTexture', 'occlusionTexture', 'emissiveTexture'):
        if k in mat: mat[k]['index'] = tex(mat[k]['index'])
    mat.pop('extensions', None); mat.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.25}
    doc['materials'].append(mat)
    doc['meshes'].append({'name': Path(path).stem, 'primitives': [{'attributes': att, 'indices': idx, 'material': len(doc['materials']) - 1}]})
    doc['nodes'].append({'name': Path(path).stem, 'mesh': len(doc['meshes']) - 1})
    jn = next(i for i, n in enumerate(doc['nodes']) if n.get('name') == joint)
    doc['nodes'][jn].setdefault('children', []).append(len(doc['nodes']) - 1)


for k, t in enumerate('abc'):
    doc, binary = G.read(GLB)
    if not doc.get('samplers'):
        doc['samplers'] = [{}]
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            for mp in prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                if k in mp['variants']: prim['material'] = mp['material']
            prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if not prim.get('extensions'): prim.pop('extensions', None)
    for m_ in doc['materials']:
        m_.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
        if m_['name'] == 'Guard_B':
            bv = add_bytes(doc, binary, BVIEW.read_bytes())
            doc['images'].append({'name': 'guard_b_viewer', 'mimeType': 'image/png', 'bufferView': bv})
            doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': 0})
            m_['pbrMetallicRoughness']['baseColorTexture']['index'] = len(doc['textures']) - 1
    for name in ATT[t]:
        attach(doc, binary, HERE / 'before' / f'{name}.glb', JOINT['halberd' if 'halberd' in name else 'plate'])
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    if not doc.get('extensions'): doc.pop('extensions', None)
    doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants'] + ['KHR_materials_specular']
    d2, b2 = RV._compact(doc, bytes(binary))
    out = HERE / 'review' / 'viewer' / f'{PREFIX}_{t}.glb'; out.parent.mkdir(parents=True, exist_ok=True)
    RV.write_glb(out, d2, b2)
    print('VIEWER', out.name, round(len(b2) / 1e6, 1), 'MB', len(d2['images']), 'images')
