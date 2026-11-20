#!/usr/bin/env python3
"""Review-viewer GLBs per colour variant (three.js has neither KHR_materials_variants selection nor region ramps):
each primitive takes its variant material, and the body's region ramps are baked into its base colour with the engine
rule (t = linear luminance normalised over the region range, colour = mix(colour, ramp(t), mask channel)).
Usage: viewer_variants.py <glb> <tag> -> review/viewer/mm6_demon_<variant>_<tag>.glb"""
import copy, io, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
HERE = Path(__file__).resolve().parents[1]
W = np.array([0.2126, 0.7152, 0.0722], np.float32)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def image(doc, binary, tex):
    v = doc['bufferViews'][doc['images'][doc['textures'][tex]['source']]['bufferView']]; s = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(binary[s:s + v['byteLength']])))


def ramp(colors, t):
    c = np.array(colors, np.float32); x = np.clip(t, 0, 1) * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2); f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


src, tag = Path(sys.argv[1]), sys.argv[2]
base_doc, base_bin = read_glb(src)
for vi, variant in enumerate(v['name'] for v in base_doc['extensions']['KHR_materials_variants']['variants']):
    doc = copy.deepcopy(base_doc); binary = bytearray(base_bin)
    for m in doc['meshes']:
        for p in m['primitives']:
            ext = p.pop('extensions', {}).get('KHR_materials_variants')
            if ext:
                p['material'] = next(x['material'] for x in ext['mappings'] if vi in x['variants'])
    doc.pop('extensions'); doc['extensionsUsed'] = [e for e in doc['extensionsUsed'] if e != 'KHR_materials_variants']
    for mi, mat in enumerate(doc['materials']):
        extras = mat.get('extras', {})
        if 'openyamm_region_ramps' not in extras or not any(p['material'] == mi for m in doc['meshes'] for p in m['primitives']):
            continue
        tex = mat['pbrMetallicRoughness']['baseColorTexture']['index']
        base = lin(np.asarray(image(doc, binary, tex).convert('RGB'), np.float32) / 255)
        mask = np.asarray(image(doc, binary, extras['openyamm_region_mask']['index']).convert('RGBA')
                          .resize(base.shape[1::-1], Image.Resampling.BILINEAR), np.float32) / 255
        lum = base @ W; out = base.copy()
        for c, reg in enumerate(extras['openyamm_region_ramps']):
            lo, hi = reg['range']; out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
        buf = io.BytesIO(); Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + .5).astype(np.uint8)).save(buf, 'PNG')
        binary.extend(b'\0' * (-len(binary) % 4))
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())}); binary.extend(buf.getvalue())
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'{variant}_baked'})
        doc['textures'].append({'source': len(doc['images']) - 1, **({'sampler': doc['textures'][tex]['sampler']} if 'sampler' in doc['textures'][tex] else {})})
        mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    write_glb(HERE / 'review/viewer' / f'mm6_{variant}_{tag}.glb', doc, bytes(binary))
    print('VIEWER', variant, tag)
