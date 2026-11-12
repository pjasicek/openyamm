#!/usr/bin/env python3
"""Review-viewer GLBs per tier (three.js has neither KHR_materials_variants nor region ramps nor attachments): from a runtime body GLB
(MM6 thief copy of mm6_gua_rebuild_claude/scripts/viewer_gua.py, no attachment), LOD0 only (LOD and shadow meshes dropped from their
nodes), each primitive on its tier material with the ramps baked into the base colour by the engine rule
(mm7_m274_texpass_claude/scripts/viewer_variants.py). Usage: viewer_thf.py <body glb> <tag> -> review/viewer/<variant>_<tag>.glb"""
import copy, io, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'mm7_m274_texpass_claude/scripts'))
from viewer_variants import bake, image  # noqa: E402
HERE = Path(__file__).resolve().parents[1]
body, tag = Path(sys.argv[1]), sys.argv[2]
bdoc, bbin = read_glb(body)
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
    doc['buffers'][0]['byteLength'] = len(binary)
    out = HERE / 'review/viewer' / f'{variant}_{tag}.glb'; write_glb(out, doc, bytes(binary)); print('VIEWER', out.name)
