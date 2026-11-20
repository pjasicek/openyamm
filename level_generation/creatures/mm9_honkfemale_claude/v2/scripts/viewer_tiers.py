#!/usr/bin/env python3
"""Review-viewer GLBs: three.js has no region ramps or per-variant head images in this viewer, so each tier is written as a copy of the
delivered export with its ramps baked into the body base colour (claude_shared/tier_textures.py) and its own head material.
Usage: viewer_tiers.py <prefix> <Mesh> <label=variant ...>   (from the project folder; writes review/viewer/<variant>.glb)"""
import io, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path.cwd()
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import tier_textures as TT
import region_variants as RV
prefix, Mesh = sys.argv[1:3]
HATS = dict(x.split('=') for x in sys.argv[3:])      # variant=<attachment glb>: shown on the head in the viewer
R = json.load(open(HERE / 'textures' / f'{prefix}_ramps.json'))
entry = R['materials'][0]
base = np.asarray(Image.open(HERE / 'textures' / f'{prefix}_basecolor_graded.png').convert('RGB'), np.float64) / 255
mask = np.stack([np.asarray(c.resize((base.shape[1], base.shape[0]), Image.BILINEAR), np.float64) / 255
                 for c in Image.open(HERE / 'textures' / entry['mask']).convert('RGBA').split()], -1)
for variant in R['variants']:
    doc, binary = RV.read_glb(HERE / 'v2' / 'export' / f'mm9_{prefix}.glb')
    binary = bytearray(binary)
    vi = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']].index(variant)
    used = None
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            ext = prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if ext:
                prim['material'] = next(m['material'] for m in ext['mappings'] if vi in m['variants'])
            if not prim.get('extensions'):
                prim.pop('extensions', None)
    img = Image.fromarray((np.clip(TT.apply(base, mask, entry['ramps'][variant]), 0, 1) * 255).astype(np.uint8))
    buf = io.BytesIO(); img.save(buf, 'PNG'); data = buf.getvalue()
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary += data
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'{Mesh}_{variant}'})
    for m in doc['materials']:
        if m['name'].startswith(Mesh) and 'Head' not in m['name'] and variant.split('_')[-1].upper() == m['name'].rsplit('_', 1)[-1].upper():
            t = doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]
            doc['textures'].append({**t, 'source': len(doc['images']) - 1})
            m['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
            m.get('extras', {}).pop('openyamm_region_mask', None); m.get('extras', {}).pop('openyamm_region_ramps', None)
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    if 'extensionsUsed' in doc:
        doc['extensionsUsed'] = [e for e in doc['extensionsUsed'] if e != 'KHR_materials_variants']
        if not doc['extensionsUsed']:
            doc.pop('extensionsUsed')
    hat = HATS.get(variant)
    if hat:
        h, hb = RV.read_glb(hat)
        def count(key):
            return len(doc.get(key, []))
        off = len(binary) + (-len(binary) % 4); binary += b'\0' * (off - len(binary)); binary += hb
        bv0, ac0, im0, tx0, sm0, mt0 = (count(k) for k in ('bufferViews', 'accessors', 'images', 'textures', 'samplers', 'materials'))
        for b in h['bufferViews']:
            doc['bufferViews'].append({**b, 'byteOffset': b.get('byteOffset', 0) + off, 'buffer': 0})
        for a in h['accessors']:
            doc['accessors'].append({**a, 'bufferView': a['bufferView'] + bv0})
        for im in h.get('images', []):
            doc['images'].append({**im, 'bufferView': im['bufferView'] + bv0})
        doc.setdefault('samplers', []).extend(h.get('samplers', []))
        for t_ in h.get('textures', []):
            doc['textures'].append({**t_, 'source': t_['source'] + im0, **({'sampler': t_['sampler'] + sm0} if 'sampler' in t_ else {})})
        for m in h['materials']:
            m = json.loads(json.dumps(m))
            for holder, key in ((m.get('pbrMetallicRoughness', {}), 'baseColorTexture'), (m.get('pbrMetallicRoughness', {}), 'metallicRoughnessTexture'), (m, 'normalTexture')):
                if key in holder:
                    holder[key]['index'] += tx0
            doc['materials'].append(m)
        hm = h['nodes'][h['scenes'][0]['nodes'][0]]['mesh']
        prims = []
        for p in h['meshes'][hm]['primitives']:
            q = json.loads(json.dumps(p))
            q['attributes'] = {k: v + ac0 for k, v in q['attributes'].items()}; q['indices'] += ac0; q['material'] += mt0
            prims.append(q)
        doc['meshes'].append({'name': 'Hat', 'primitives': prims})
        doc['nodes'].append({'name': 'HatView', 'mesh': len(doc['meshes']) - 1})
        hi = next(i for i, n in enumerate(doc['nodes']) if n.get('name') == 'Bip01 Head')
        doc['nodes'][hi].setdefault('children', []).append(len(doc['nodes']) - 1)
    RV.write_glb(HERE / 'review' / 'viewer' / f'{variant}.glb', doc, bytes(binary))
    print('viewer', variant, [m['name'] for m in doc['materials']][:8])
