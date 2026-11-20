#!/usr/bin/env python3
"""Add the (variant-baked) sword to a (variant-baked) review-viewer body GLB as a rigid skinned primitive on the `Sword`
joint, so three.js shows the held sword (the engine attaches mm8_m444_sword.glb to that node at runtime). Sword vertices
go to bind space through the joint's inverse bind matrix. Usage: merge_sword.py <body viewer glb> <sword viewer glb> <out>"""
import copy, struct, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402
body, bbin = read_glb(Path(sys.argv[1])); bbin = bytearray(bbin); sword, sbin = read_glb(Path(sys.argv[2]))
node = next(n for n in body['nodes'] if n.get('name') == 'Smuggler'); skin = body['skins'][node['skin']]
joint = [body['nodes'][k]['name'] for k in skin['joints']].index('Sword')
ibm = np.array(struct.unpack('<16f', accessor_bytes(body, bbin, skin['inverseBindMatrices'])[joint * 64:(joint + 1) * 64]),
               np.float64).reshape(4, 4).T
bind = np.linalg.inv(ibm)
sprim = sword['meshes'][0]['primitives'][0]
get = lambda a: accessor_bytes(sword, sbin, sprim['attributes'][a])
spos = np.frombuffer(get('POSITION'), np.float32).reshape(-1, 3); snrm = np.frombuffer(get('NORMAL'), np.float32).reshape(-1, 3)
wpos = (np.c_[spos, np.ones(len(spos))] @ bind.T)[:, :3].astype(np.float32)
wnrm = snrm @ bind[:3, :3].T; wnrm = (wnrm / np.linalg.norm(wnrm, axis=1, keepdims=True)).astype(np.float32)


def copy_image(index):
    v = sword['bufferViews'][sword['images'][index]['bufferView']]; data = sbin[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']]
    bbin.extend(b'\0' * (-len(bbin) % 4))
    body['bufferViews'].append({'buffer': 0, 'byteOffset': len(bbin), 'byteLength': len(data)}); bbin.extend(data)
    body['images'].append({'bufferView': len(body['bufferViews']) - 1, 'mimeType': sword['images'][index].get('mimeType', 'image/png')})
    body['textures'].append({'source': len(body['images']) - 1}); return len(body['textures']) - 1


smat = copy.deepcopy(sword['materials'][sprim['material']]); smat.pop('extras', None); smat['name'] = 'Sword_viewer'
for key in ('baseColorTexture', 'metallicRoughnessTexture'):
    if key in smat.get('pbrMetallicRoughness', {}):
        smat['pbrMetallicRoughness'][key] = {'index': copy_image(sword['textures'][smat['pbrMetallicRoughness'][key]['index']]['source'])}
if 'normalTexture' in smat:
    smat['normalTexture'] = {'index': copy_image(sword['textures'][smat['normalTexture']['index']]['source'])}
body['materials'].append(smat)
bp = body['meshes'][node['mesh']]['primitives'][0]
jacc = body['accessors'][bp['attributes']['JOINTS_0']]; wacc = body['accessors'][bp['attributes']['WEIGHTS_0']]
n = len(wpos); joints = np.zeros((n, 4), {5121: np.uint8, 5123: np.uint16}[jacc['componentType']]); joints[:, 0] = joint
weights = np.zeros((n, 4), np.float32); weights[:, 0] = 1
attrs = {'POSITION': append_accessor(body, bbin, dict(sword['accessors'][sprim['attributes']['POSITION']], min=wpos.min(0).tolist(), max=wpos.max(0).tolist()), wpos.tobytes()),
         'NORMAL': append_accessor(body, bbin, sword['accessors'][sprim['attributes']['NORMAL']], wnrm.tobytes()),
         'TEXCOORD_0': append_accessor(body, bbin, sword['accessors'][sprim['attributes']['TEXCOORD_0']], get('TEXCOORD_0')),
         'JOINTS_0': append_accessor(body, bbin, {k: v for k, v in dict(jacc, count=n).items() if k not in ('min', 'max', 'bufferView', 'byteOffset')}, joints.tobytes()),
         'WEIGHTS_0': append_accessor(body, bbin, {k: v for k, v in dict(wacc, count=n).items() if k not in ('min', 'max', 'bufferView', 'byteOffset')}, weights.tobytes())}
if 'JOINTS_1' in bp['attributes']:
    attrs['JOINTS_1'] = append_accessor(body, bbin, {k: v for k, v in dict(jacc, count=n).items() if k not in ('min', 'max')}, np.zeros((n, 4), joints.dtype).tobytes())
    attrs['WEIGHTS_1'] = append_accessor(body, bbin, {k: v for k, v in dict(wacc, count=n).items() if k not in ('min', 'max')}, np.zeros((n, 4), np.float32).tobytes())
ind = append_accessor(body, bbin, sword['accessors'][sprim['indices']], accessor_bytes(sword, sbin, sprim['indices']))
body['meshes'][node['mesh']]['primitives'].append({'attributes': attrs, 'indices': ind, 'material': len(body['materials']) - 1})
write_glb(Path(sys.argv[3]), body, bytes(bbin)); print('MERGED sword', n, 'vertices on joint', joint, '->', sys.argv[3])
