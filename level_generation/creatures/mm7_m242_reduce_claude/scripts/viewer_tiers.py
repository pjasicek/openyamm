#!/usr/bin/env python3
"""Review-viewer GLBs for the reduction (three.js has no region ramps): each KHR_materials_variants tier material of
<glb> (M242_A/B/C, one region: the robe) is baked into its base colour with the engine rule (t = linear luminance
normalised over the region's range, colour = mix(colour, ramp(t), mask channel); ramps from the material extras),
and only the full-detail mesh is kept (LOD and shadow meshes dropped, buffer compacted).
Writes review/viewer/mm7_m242_<label>_<a|b|c>.glb inside this project only. Usage: viewer_tiers.py <glb> <label>"""
import copy, io, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
W = np.array([0.2126, 0.7152, 0.0722], np.float32)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def ramp(colors, t):
    c = np.array(colors, np.float32); x = np.clip(t, 0, 1) * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2); f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


src, label = Path(sys.argv[1]), sys.argv[2]
D, B = read_glb(src); B = bytes(B)
img = lambda i: Image.open(io.BytesIO(B[D['bufferViews'][D['images'][i]['bufferView']].get('byteOffset', 0):][:D['bufferViews'][D['images'][i]['bufferView']]['byteLength']]))
for v, mat in enumerate(D['materials']):
    tier = mat['name'].split('_')[-1].lower()
    doc = copy.deepcopy(D); binary = bytearray()
    base_img = img(D['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source']).convert('RGBA')
    rgba = np.asarray(base_img, np.float32) / 255
    mask = np.stack([np.asarray(ch.resize(base_img.size, Image.BILINEAR), np.float32) / 255
                     for ch in img(D['textures'][mat['extras']['openyamm_region_mask']['index']]['source']).convert('RGBA').split()], -1)
    base = lin(rgba[..., :3]); lum = base @ W; out = base.copy()
    for c, reg in enumerate(mat['extras']['openyamm_region_ramps']):
        lo, hi = reg['range']
        out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
    buf = io.BytesIO(); Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + .5).astype(np.uint8)).save(buf, 'PNG')
    # keep only the node mesh, one material (the baked tier), its textures
    node = next(n for n in doc['nodes'] if 'mesh' in n)
    mesh = doc['meshes'][node['mesh']]; mesh.pop('extras', None)
    for p in mesh['primitives']:
        p.pop('extensions', None); p['material'] = 0
    doc.pop('extensionsUsed', None); doc.pop('extensions', None)
    m = copy.deepcopy(mat); m.pop('extras', None); m['name'] = f'M242_{tier.upper()}_baked'
    doc['meshes'] = [mesh]; node['mesh'] = 0; doc['materials'] = [m]
    acc = sorted({i for p in mesh['primitives'] for i in list(p['attributes'].values()) + [p['indices']]}
                 | {s['inverseBindMatrices'] for s in doc['skins']}
                 | {i for a in doc.get('animations', []) for s in a['samplers'] for i in (s['input'], s['output'])})
    texs = [m['pbrMetallicRoughness']['baseColorTexture']['index'], m['pbrMetallicRoughness']['metallicRoughnessTexture']['index'],
            m['normalTexture']['index']]
    newimgs, views = [], []

    def put(data):
        binary.extend(b'\0' * (-len(binary) % 4)); views.append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
        binary.extend(data); return len(views) - 1
    amap = {}
    accessors = []
    for i in acc:
        a = copy.deepcopy(doc['accessors'][i]); bv = doc['bufferViews'][a['bufferView']]
        nv = put(B[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])
        if 'byteStride' in bv:
            views[nv]['byteStride'] = bv['byteStride']
        a['bufferView'] = nv; amap[i] = len(accessors); accessors.append(a)
    textures = []
    for k, t in enumerate(texs):
        si = D['textures'][t]['source']; bv = D['bufferViews'][D['images'][si]['bufferView']]
        data = buf.getvalue() if k == 0 else B[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]
        newimgs.append({'bufferView': put(data), 'mimeType': 'image/png'})
        textures.append({'source': k, 'sampler': D['textures'][t].get('sampler', 0)})
    m['pbrMetallicRoughness']['baseColorTexture']['index'] = 0
    m['pbrMetallicRoughness']['metallicRoughnessTexture']['index'] = 1; m['normalTexture']['index'] = 2
    for p in mesh['primitives']:
        p['attributes'] = {s: amap[i] for s, i in p['attributes'].items()}; p['indices'] = amap[p['indices']]
    for s in doc['skins']:
        s['inverseBindMatrices'] = amap[s['inverseBindMatrices']]
    for a in doc.get('animations', []):
        for s in a['samplers']:
            s['input'] = amap[s['input']]; s['output'] = amap[s['output']]
    doc.update(accessors=accessors, bufferViews=views, images=newimgs, textures=textures)
    out_path = ROOT / 'review' / 'viewer' / f'mm7_m242_{label}_{tier}.glb'
    write_glb(out_path, doc, bytes(binary)); print('VIEWER', out_path.name, f'{out_path.stat().st_size / 1e6:.1f} MB')
