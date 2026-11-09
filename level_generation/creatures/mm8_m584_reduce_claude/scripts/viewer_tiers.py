#!/usr/bin/env python3
"""Browser review GLBs for each Raven Man tier: the engine's region ramps (each material's openyamm_region_ramps over
the shared openyamm_region_mask, as mm8_m560_reduce_claude/scripts/viewer_tiers.py) baked into a per-tier base colour,
that tier's material made the default, LOD/shadow meshes left out (the browser draws the node mesh only).
Usage: viewer_tiers.py <glb> <tag> -> review/viewer/raven_<a|b|c>_<tag>.glb"""
import copy, io, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
GLB, TAG = Path(sys.argv[1]), sys.argv[2]
W = np.array([0.2126, 0.7152, 0.0722], np.float32)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def read_glb(path):
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write_glb(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4)
    doc['buffers'][0]['byteLength'] = len(binary)
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                     + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)


def image(doc, binary, texture):
    v = doc['bufferViews'][doc['images'][doc['textures'][texture]['source']]['bufferView']]
    return Image.open(io.BytesIO(bytes(binary[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])))


def ramp(colors, t):
    c = np.array(colors, np.float32); x = np.clip(t, 0, 1) * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2); f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


src_doc, src_bin = read_glb(GLB)
body = next(n for n in src_doc['nodes'] if n.get('name') == 'Body')
for tier, mi in (('a', 0), ('b', 1), ('c', 2)):
    doc, binary = copy.deepcopy(src_doc), bytearray(src_bin)
    mat = doc['materials'][mi]
    base_im = image(doc, binary, mat['pbrMetallicRoughness']['baseColorTexture']['index']).convert('RGB')
    base = lin(np.asarray(base_im, np.float32) / 255)
    mask = np.stack([np.asarray(ch.resize(base_im.size, Image.BILINEAR), np.float32) / 255 for ch in
                     image(doc, binary, mat['extras']['openyamm_region_mask']['index']).convert('RGBA').split()], -1)
    lum = base @ W; out = base.copy()
    for c, reg in enumerate(mat['extras']['openyamm_region_ramps']):
        lo, hi = reg['range']
        out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
    buf = io.BytesIO(); Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + .5).astype(np.uint8)).save(buf, 'PNG')
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
    binary += buf.getvalue()
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'raven_{tier}'})
    info = mat['pbrMetallicRoughness']['baseColorTexture']
    doc['textures'].append(dict(doc['textures'][info['index']], source=len(doc['images']) - 1))
    info['index'] = len(doc['textures']) - 1
    for p in doc['meshes'][body['mesh']]['primitives']:
        p['material'] = mi
    write_glb(HERE / 'review' / 'viewer' / f'raven_{tier}_{TAG}.glb', doc, binary)
    print('VIEWER', f'raven_{tier}_{TAG}.glb')
