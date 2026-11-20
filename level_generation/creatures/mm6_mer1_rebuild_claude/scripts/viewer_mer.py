#!/usr/bin/env python3
"""Review-viewer GLBs per tier (three.js has neither KHR_materials_variants nor region ramps nor attachments): from a runtime body GLB
and its club attachment, LOD0 only (LOD and shadow meshes dropped from their nodes), each primitive on its tier material with
the ramps baked into the base colour by the engine rule (mm7_m274_texpass_claude/scripts/viewer_variants.py), and the club added
to LOD0 as a primitive rigid on Ybasesword (its vertices taken from Ybasesword's bind frame into the skin space).
Usage: viewer_gua.py <body glb> <club glb> <tag> -> review/viewer/<variant>_<tag>.glb"""
import copy, io, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'mm7_m274_texpass_claude/scripts'))
from viewer_variants import bake, image  # noqa: E402
HERE = Path(__file__).resolve().parents[1]
body, hal, tag = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
bdoc, bbin = read_glb(body); hdoc, hbin = read_glb(hal)
TY = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}; NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def acc(doc, binary, i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0); n = NC[a['type']]
    return np.frombuffer(bytes(binary[off:off + a['count'] * n * np.dtype(TY[a['componentType']]).itemsize]), TY[a['componentType']]).reshape(a['count'], n) if n > 1 else \
        np.frombuffer(bytes(binary[off:off + a['count'] * np.dtype(TY[a['componentType']]).itemsize]), TY[a['componentType']])


def add(doc, binary, arr, ctype, typ, target=None):
    data = np.ascontiguousarray(arr).tobytes(); binary.extend(b'\0' * (-len(binary) % 4))
    bv = {'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}
    if target: bv['target'] = target
    doc['bufferViews'].append(bv); binary.extend(data)
    a = {'bufferView': len(doc['bufferViews']) - 1, 'componentType': ctype, 'count': len(arr), 'type': typ}
    if typ == 'VEC3' and ctype == 5126: a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
    doc['accessors'].append(a); return len(doc['accessors']) - 1


names = [n.get('name') for n in bdoc['nodes']]; skin = bdoc['skins'][0]
jn_ = [names[k] for k in skin['joints']]; ji = jn_.index("Club")   # before: the old rig's Club joint
IBM = acc(bdoc, bbin, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
M = np.linalg.inv(IBM[ji].astype(float))
hp = hdoc['meshes'][0]['primitives'][0]
HP = acc(hdoc, hbin, hp['attributes']['POSITION']).astype(float); HN = acc(hdoc, hbin, hp['attributes']['NORMAL']).astype(float)
HUV = acc(hdoc, hbin, hp['attributes']['TEXCOORD_0']); HI = acc(hdoc, hbin, hp['indices']).astype(np.uint32)
P = HP @ M[:3, :3].T + M[:3, 3]; N = HN @ M[:3, :3].T; N /= np.linalg.norm(N, axis=1, keepdims=True)
hvar = hp.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])
variants = [v['name'] for v in bdoc['extensions']['KHR_materials_variants']['variants']]
for vi, variant in enumerate(variants):
    doc = copy.deepcopy(bdoc); binary = bytearray(bbin)
    for node in doc['nodes']:
        if 'mesh' in node and any(k in doc['meshes'][node['mesh']].get('name', '') for k in ('LOD', 'Shadow')): node.pop('mesh')
    for m in doc['meshes']:
        for p in m['primitives']:
            ext = p.pop('extensions', {}).get('KHR_materials_variants')
            if ext: p['material'] = next(x['material'] for x in ext['mappings'] if vi in x['variants'])
    doc.pop('extensions'); doc['extensionsUsed'] = [e for e in doc['extensionsUsed'] if e != 'KHR_materials_variants']
    # halberd material of this tier: its own images, ramps baked
    hm = copy.deepcopy(hdoc['materials'][next((x['material'] for x in hvar if vi in x['variants']), hp.get('material', 0))])
    ex = hm.get('extras', {})
    col = image(hdoc, hbin, hm['pbrMetallicRoughness']['baseColorTexture']['index']).convert('RGB')
    if 'openyamm_region_ramps' in ex: col = Image.fromarray(bake(col, image(hdoc, hbin, ex['openyamm_region_mask']['index']), ex['openyamm_region_ramps']))
    texs = {}
    for key, img in (('base', col), ('mr', image(hdoc, hbin, hm['pbrMetallicRoughness']['metallicRoughnessTexture']['index']) if 'metallicRoughnessTexture' in hm['pbrMetallicRoughness'] else None),
                     ('n', image(hdoc, hbin, hm['normalTexture']['index']) if 'normalTexture' in hm else None)):
        if img is None: continue
        buf = io.BytesIO(); img.save(buf, 'PNG'); binary.extend(b'\0' * (-len(binary) % 4))
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())}); binary.extend(buf.getvalue())
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'club_{key}_{variant}'})
        doc['textures'].append({'source': len(doc['images']) - 1}); texs[key] = len(doc['textures']) - 1
    hm['pbrMetallicRoughness']['baseColorTexture'] = {'index': texs['base']}
    if 'mr' in texs: hm['pbrMetallicRoughness']['metallicRoughnessTexture'] = {'index': texs['mr']}
    if 'n' in texs: hm['normalTexture'] = {'index': texs['n']}
    hm.pop('extras', None); hm['name'] = 'Club_viewer'; doc['materials'].append(hm)
    for mi, mat in enumerate(doc['materials']):
        extras = mat.get('extras', {})
        used = any(p.get('material') == mi for nd in doc['nodes'] if 'mesh' in nd for p in doc['meshes'][nd['mesh']]['primitives'])
        if 'openyamm_region_ramps' not in extras or not used: continue
        tex = mat['pbrMetallicRoughness']['baseColorTexture']['index']
        out = bake(image(doc, binary, tex).convert('RGB'), image(doc, binary, extras['openyamm_region_mask']['index']), extras['openyamm_region_ramps'])
        buf = io.BytesIO(); Image.fromarray(out).save(buf, 'PNG'); binary.extend(b'\0' * (-len(binary) % 4))
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())}); binary.extend(buf.getvalue())
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'{variant}_baked'})
        doc['textures'].append({'source': len(doc['images']) - 1}); mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    lod0 = next(nd['mesh'] for nd in doc['nodes'] if 'mesh' in nd and 'skin' in nd)
    prim = {'attributes': {'POSITION': add(doc, binary, P.astype(np.float32), 5126, 'VEC3', 34962), 'NORMAL': add(doc, binary, N.astype(np.float32), 5126, 'VEC3', 34962),
                           'TEXCOORD_0': add(doc, binary, HUV.astype(np.float32), 5126, 'VEC2', 34962),
                           'JOINTS_0': add(doc, binary, np.tile(np.array([ji, 0, 0, 0], np.uint16), (len(P), 1)), 5123, 'VEC4', 34962),
                           'WEIGHTS_0': add(doc, binary, np.tile(np.array([1, 0, 0, 0], np.float32), (len(P), 1)), 5126, 'VEC4', 34962)},
            'indices': add(doc, binary, HI.ravel(), 5125, 'SCALAR', 34963), 'material': len(doc['materials']) - 1}
    doc['meshes'][lod0]['primitives'].append(prim)
    doc['buffers'][0]['byteLength'] = len(binary)
    out = HERE / 'review/viewer' / f'{variant}_{tag}.glb'; write_glb(out, doc, bytes(binary)); print('VIEWER', out.name)
