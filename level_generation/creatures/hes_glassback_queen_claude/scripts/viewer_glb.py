#!/usr/bin/env python3
"""Review-viewer GLB (three.js has no region ramps and no attachments): from a runtime GLB keep the full-detail skinned
mesh(es) only (LOD and shadow meshes dropped), choose each primitive's material for one KHR_materials_variants tier,
bake region ramps into the base colour with the engine rule (as hes_glassback_reduce_claude/scripts/viewer_tiers.py:
t = linear luminance normalised over the region's range, colour = mix(colour, ramp(t), mask channel)), and merge
attachment GLBs (their full-detail mesh, the same tier) as children of their joints (attachments are authored in the
joint's space, as the engine draws them). Clips, skins and emission are kept (an unlit glow material shows its emission as its base colour, as three.js
draws unlit materials by base colour only); the buffer is rebuilt.
Usage: viewer_glb.py <runtime.glb> <out.glb> [--variant NAME] [--attach <attachment.glb>:<joint> ...]"""
import argparse
import copy
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

W = np.array([0.2126, 0.7152, 0.0722], np.float32)
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)  # noqa: E731
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)  # noqa: E731


def ramp(colors, t):
    c = np.array(colors, np.float32); x = np.clip(t, 0, 1) * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2); f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


class Builder:
    """Collects accessors, images and materials from source documents into one new document."""

    def __init__(self):
        self.binary = bytearray(); self.views = []; self.accessors = []; self.images = []; self.textures = []
        self.materials = []; self.samplers = [{}]

    def put(self, data, stride=None):
        self.binary.extend(b'\0' * (-len(self.binary) % 4))
        v = {'buffer': 0, 'byteOffset': len(self.binary), 'byteLength': len(data)}
        if stride:
            v['byteStride'] = stride
        self.views.append(v); self.binary.extend(data)
        return len(self.views) - 1

    def accessor(self, doc, b, i, cache):
        key = (id(doc), i)
        if key not in cache:
            a = copy.deepcopy(doc['accessors'][i]); bv = doc['bufferViews'][a['bufferView']]
            o = bv.get('byteOffset', 0)
            a['bufferView'] = self.put(bytes(b[o:o + bv['byteLength']]), bv.get('byteStride'))
            self.accessors.append(a); cache[key] = len(self.accessors) - 1
        return cache[key]

    def image_bytes(self, doc, b, tex):
        img = doc['images'][doc['textures'][tex]['source']]; bv = doc['bufferViews'][img['bufferView']]
        o = bv.get('byteOffset', 0)
        return bytes(b[o:o + bv['byteLength']])

    def texture(self, data):
        self.images.append({'bufferView': self.put(data), 'mimeType': 'image/png'})
        self.textures.append({'source': len(self.images) - 1, 'sampler': 0})
        return len(self.textures) - 1

    def material(self, doc, b, mi, cache):
        key = (id(doc), mi)
        if key in cache:
            return cache[key]
        m = copy.deepcopy(doc['materials'][mi]); ex = m.pop('extras', {}) or {}
        pbr = m.get('pbrMetallicRoughness', {})
        if 'baseColorTexture' in pbr:
            data = self.image_bytes(doc, b, pbr['baseColorTexture']['index'])
            if 'openyamm_region_mask' in ex:
                base_img = Image.open(io.BytesIO(data)).convert('RGBA')
                rgba = np.asarray(base_img, np.float32) / 255
                mimg = Image.open(io.BytesIO(self.image_bytes(doc, b, ex['openyamm_region_mask']['index']))).convert('RGBA')
                mask = np.stack([np.asarray(ch.resize(base_img.size, Image.BILINEAR), np.float32) / 255
                                 for ch in mimg.split()], -1)
                base = lin(rgba[..., :3]); lum = base @ W; out = base.copy()
                for c, reg in enumerate(ex['openyamm_region_ramps']):
                    lo, hi = reg['range']
                    out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
                buf = io.BytesIO()
                Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + .5).astype(np.uint8)).save(buf, 'PNG')
                data = buf.getvalue()
            pbr['baseColorTexture'] = {'index': self.texture(data)}
        for slot in ('metallicRoughnessTexture',):
            if slot in pbr:
                pbr[slot] = {'index': self.texture(self.image_bytes(doc, b, pbr[slot]['index']))}
        for slot in ('normalTexture', 'emissiveTexture', 'occlusionTexture'):
            if slot in m:
                m[slot] = {**m[slot], 'index': self.texture(self.image_bytes(doc, b, m[slot]['index']))}
        m.get('extensions', {}).pop('KHR_materials_variants', None)
        if 'KHR_materials_unlit' in m.get('extensions', {}):
            # three.js draws an unlit material by its base colour only: show the glow as its emission
            strength = m['extensions'].get('KHR_materials_emissive_strength', {}).get('emissiveStrength', 1.0)
            pbr['baseColorFactor'] = [min(1.0, c * strength) for c in m.get('emissiveFactor', [0, 0, 0])] + [1.0]
        self.materials.append(m); cache[key] = len(self.materials) - 1
        return cache[key]


def variant_material(doc, prim, variant):
    if variant and 'KHR_materials_variants' in doc.get('extensions', {}):
        names = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']]
        if variant in names:
            k = names.index(variant)
            for mp in prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                if k in mp['variants']:
                    return mp['material']
    return prim['material']


def lod0_meshes(doc):
    far = {i for m in doc['meshes'] for i in (m.get('extras') or {}).get('openyamm_lods', [])}
    far |= {i for m in doc['meshes'] for i in [(m.get('extras') or {}).get('openyamm_shadow_mesh')] if i is not None}
    return far


def copy_mesh(B, doc, b, mesh, variant, acache, mcache):
    prims = []
    for p in mesh['primitives']:
        q = {'attributes': {s: B.accessor(doc, b, i, acache) for s, i in p['attributes'].items()},
             'indices': B.accessor(doc, b, p['indices'], acache), 'material': B.material(doc, b, variant_material(doc, p, variant), mcache)}
        if 'mode' in p:
            q['mode'] = p['mode']
        prims.append(q)
    return {'name': mesh.get('name', 'mesh'), 'primitives': prims}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--variant'); ap.add_argument('--attach', nargs='*', default=[])
    a = ap.parse_args()
    D, Bin = read_glb(Path(a.src)); Bin = bytes(Bin)
    B = Builder(); acache, mcache = {}, {}
    doc = copy.deepcopy(D)
    far = lod0_meshes(D)
    meshes, mesh_map = [], {}
    for n in doc['nodes']:
        if 'mesh' not in n:
            continue
        name = D['meshes'][n['mesh']].get('name', '')
        if n['mesh'] in far or 'Shadow' in name or '_LOD' in name or 'skin' not in n:
            del n['mesh']; n.pop('skin', None) if 'skin' in n and 'mesh' not in n else None
            continue
        if n['mesh'] not in mesh_map:
            meshes.append(copy_mesh(B, D, Bin, D['meshes'][n['mesh']], a.variant, acache, mcache))
            mesh_map[n['mesh']] = len(meshes) - 1
        n['mesh'] = mesh_map[n['mesh']]
    for s in doc['skins']:
        s['inverseBindMatrices'] = B.accessor(D, Bin, s['inverseBindMatrices'], acache)
    for an in doc.get('animations', []):
        for s in an['samplers']:
            s['input'] = B.accessor(D, Bin, s['input'], acache); s['output'] = B.accessor(D, Bin, s['output'], acache)
    for spec in a.attach:
        path, joint = spec.rsplit(':', 1)
        AD, AB = read_glb(Path(path)); AB = bytes(AB)
        afar = lod0_meshes(AD)
        jn = next(i for i, n in enumerate(doc['nodes']) if n.get('name', '').lower() == joint.lower())
        for n in AD['nodes']:
            if 'mesh' not in n or n['mesh'] in afar or '_LOD' in AD['meshes'][n['mesh']].get('name', ''):
                continue
            meshes.append(copy_mesh(B, AD, AB, AD['meshes'][n['mesh']], a.variant, {}, {}))
            doc['nodes'].append({'name': f'Attach_{Path(path).stem}', 'mesh': len(meshes) - 1})
            doc['nodes'][jn].setdefault('children', []).append(len(doc['nodes']) - 1)
    doc['meshes'] = meshes
    doc.update(accessors=B.accessors, bufferViews=B.views, images=B.images, textures=B.textures,
               materials=B.materials, samplers=B.samplers, buffers=[{'byteLength': len(B.binary)}])
    doc.pop('extensions', None)
    doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants']
    if any('KHR_materials_unlit' in m.get('extensions', {}) for m in B.materials) and 'KHR_materials_unlit' not in doc['extensionsUsed']:
        doc['extensionsUsed'].append('KHR_materials_unlit')
    if any('KHR_materials_emissive_strength' in m.get('extensions', {}) for m in B.materials) \
            and 'KHR_materials_emissive_strength' not in doc['extensionsUsed']:
        doc['extensionsUsed'].append('KHR_materials_emissive_strength')
    doc.pop('extensionsRequired', None)
    write_glb(Path(a.out), doc, bytes(B.binary))
    print('VIEWER', Path(a.out).name, f'{len(B.binary) / 1e6:.1f} MB', 'meshes', len(meshes), 'materials', len(B.materials))


if __name__ == '__main__':
    main()
