#!/usr/bin/env python3
"""Review-viewer GLBs of the reduced Ether Knight, one per tier (review/viewer/mm8_m604_<tier>_r75.glb): the body
export's region ramps baked into its base colour (the same formula as mm8_m604_claude/scripts/viewer_tiers.py) and
the reduced sword added as a rigid skinned primitive on the `Sword` joint (the installed viewer files carry it the
same way). The installed rows reuse mm8_m604_claude/review/viewer/mm8_m604_<tier>.glb unchanged.
Usage: viewer_build.py"""
import copy
import hashlib
import io
import json
import shutil
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

V = HERE / 'review/viewer'; V.mkdir(parents=True, exist_ok=True)
W = np.array([0.2126, 0.7152, 0.0722], np.float32)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def ramp(colors, t):
    c = np.array(colors, np.float32); x = np.clip(t, 0, 1) * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2); f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


def image(doc, binary, index):
    view = doc['bufferViews'][doc['images'][index]['bufferView']]
    start = view.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(binary[start:start + view['byteLength']])))


def add_image(doc, binary, im, name):
    buf = io.BytesIO(); im.save(buf, 'PNG')
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
    binary.extend(buf.getvalue())
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': name})
    return len(doc['images']) - 1


import os
body, bbin = read_glb(HERE / os.environ.get('VIEW_BODY', 'export/mm8_m604.glb'))
SUFFIX = os.environ.get('VIEW_SUFFIX', 'r75')
sword, sbin = read_glb(HERE / 'export/mm8_m604_sword.glb')
node = next(n for n in body['nodes'] if n.get('name') == 'EtherKnight')
skin = body['skins'][node['skin']]
joint = [body['nodes'][k]['name'] for k in skin['joints']].index('Sword')
ibm = np.array(struct.unpack('<16f', accessor_bytes(body, bbin, skin['inverseBindMatrices'])[joint * 64:(joint + 1) * 64]),
               np.float64).reshape(4, 4).T
bind = np.linalg.inv(ibm)
sprim = sword['meshes'][0]['primitives'][0]
spos = np.frombuffer(accessor_bytes(sword, sbin, sprim['attributes']['POSITION']), np.float32).reshape(-1, 3)
snrm = np.frombuffer(accessor_bytes(sword, sbin, sprim['attributes']['NORMAL']), np.float32).reshape(-1, 3)
wpos = (np.c_[spos, np.ones(len(spos))] @ bind.T)[:, :3].astype(np.float32)
wnrm = snrm @ bind[:3, :3].T; wnrm = (wnrm / np.linalg.norm(wnrm, axis=1, keepdims=True)).astype(np.float32)
body_prim = body['meshes'][node['mesh']]['primitives'][0]
jacc = body['accessors'][body_prim['attributes']['JOINTS_0']]; wacc = body['accessors'][body_prim['attributes']['WEIGHTS_0']]
jcode = {5121: np.uint8, 5123: np.uint16}[jacc['componentType']]
base = image(body, bbin, body['textures'][body['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']]['source'])
rgba = np.asarray(base.convert('RGBA'), np.float32) / 255
mask_index = body['textures'][body['materials'][0]['extras']['openyamm_region_mask']['index']]['source']
mask = np.asarray(image(body, bbin, mask_index).convert('RGBA'), np.float32) / 255
models = []
for k, variant in enumerate(v['name'] for v in body['extensions']['KHR_materials_variants']['variants']):
    doc = copy.deepcopy(body); binary = bytearray(bbin)
    ramps = doc['materials'][k]['extras']['openyamm_region_ramps']
    col = lin(rgba[..., :3]); lum = col @ W; out = col.copy()
    for c, reg in enumerate(ramps):
        lo, hi = reg['range']
        out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
    baked = Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + .5).astype(np.uint8))
    mat = copy.deepcopy(doc['materials'][0]); mat['name'] = f'EtherKnight_{variant}'
    mat.pop('extras', None)
    tex = copy.deepcopy(doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']])
    tex['source'] = add_image(doc, binary, baked, f'm604_{variant}_viewer')
    doc['textures'].append(tex); mat['pbrMetallicRoughness']['baseColorTexture']['index'] = len(doc['textures']) - 1
    doc['materials'].append(mat); body_mat = len(doc['materials']) - 1
    # sword material and its images
    smat = copy.deepcopy(sword['materials'][0])
    for key in ('baseColorTexture', 'metallicRoughnessTexture'):
        if key in smat.get('pbrMetallicRoughness', {}):
            info = smat['pbrMetallicRoughness'][key]; st = sword['textures'][info['index']]
            doc['textures'].append({**({'sampler': 0} if 'sampler' in st and doc.get('samplers') else {}),
                                    'source': add_image(doc, binary, image(sword, sbin, st['source']), f'sword_{key}')})
            info['index'] = len(doc['textures']) - 1
    if 'normalTexture' in smat:
        st = sword['textures'][smat['normalTexture']['index']]
        doc['textures'].append({'source': add_image(doc, binary, image(sword, sbin, st['source']), 'sword_normal')})
        smat['normalTexture']['index'] = len(doc['textures']) - 1
    doc['materials'].append(smat); sword_mat = len(doc['materials']) - 1
    mesh = doc['meshes'][node['mesh']]
    prim = mesh['primitives'][0]; prim['material'] = body_mat; prim.pop('extensions', None)
    n = len(wpos)
    joints = np.zeros((n, 4), jcode); joints[:, 0] = joint
    weights = np.zeros((n, 4), np.float32); weights[:, 0] = 1
    pacc = dict(sword['accessors'][sprim['attributes']['POSITION']], min=wpos.min(0).tolist(), max=wpos.max(0).tolist())
    attrs = {'POSITION': append_accessor(doc, binary, pacc, wpos.tobytes()),
             'NORMAL': append_accessor(doc, binary, sword['accessors'][sprim['attributes']['NORMAL']], wnrm.tobytes()),
             'TEXCOORD_0': append_accessor(doc, binary, sword['accessors'][sprim['attributes']['TEXCOORD_0']],
                                           accessor_bytes(sword, sbin, sprim['attributes']['TEXCOORD_0'])),
             'JOINTS_0': append_accessor(doc, binary, dict(jacc, count=n), joints.tobytes()),
             'WEIGHTS_0': append_accessor(doc, binary, dict(wacc, count=n), weights.tobytes())}
    for a in ('JOINTS_0', 'WEIGHTS_0'):
        doc['accessors'][attrs[a]].pop('min', None); doc['accessors'][attrs[a]].pop('max', None)
    ind = append_accessor(doc, binary, sword['accessors'][sprim['indices']], accessor_bytes(sword, sbin, sprim['indices']))
    mesh['primitives'].append({'attributes': attrs, 'indices': ind, 'material': sword_mat})
    doc.pop('extensions', None); doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants']
    for m in doc['meshes']:
        for p in m['primitives']:
            p.pop('extensions', None)
    out_path = V / f'mm8_m604_{variant[-1]}_{SUFFIX}.glb'; write_glb(out_path, doc, bytes(binary))
    shutil.copy(HERE.parent / 'mm8_m604_claude/review/viewer' / f'mm8_m604_{variant[-1]}.glb', V / f'mm8_m604_{variant[-1]}_r100.glb')
    labels = {'a': 'Ether Knight — green', 'b': 'Ether Champion — purple', 'c': 'Ether Lord — red'}
    for tag, label in (('r100', f'installed · 11,114 + sword 1,260'), ('r75', f'reduced · 8,332 + sword 774')):
        g = V / f'mm8_m604_{variant[-1]}_{tag}.glb'; h = hashlib.sha256(g.read_bytes()).hexdigest()
        models.append({'id': f'm604_{variant[-1]}_{tag}', 'label': f'{labels[variant[-1]]} · {label}',
                       'url': f'{g.name}?v={h[:12]}', 'sha256': h, 'revision': 'reduce-1'})
    print('VIEWER', variant, out_path.name)
m = json.loads((HERE.parent / 'mm8_m604_claude/review/viewer/manifest.json').read_text())
text = json.dumps(m).replace('"../../references_native/', '"../../../mm8_m604_claude/references_native/')
m = json.loads(text)
m.update(revision='reduce-1', default_model='m604_a_r75', models=models, model=models[1]['url'],
         model_sha256=models[1]['sha256'], feedback='../feedback/user_feedback.json')
(V / 'manifest.json').write_text(json.dumps(m, indent=1) + '\n')
print('MANIFEST', len(models), 'models')
