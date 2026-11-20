#!/usr/bin/env python3
"""Review-viewer GLBs per colour variant (three.js has neither KHR_materials_variants selection nor region ramps):
each primitive takes its variant material, and the body's region ramps are baked into its base colour with the engine
rule (t = linear luminance normalised over the region range, colour = mix(colour, ramp(t), mask channel)).
With an attachment (<attachment.glb>:<joint node>, MM8 Salamander polearm) its level-zero mesh is baked the same way
per variant and added as a child mesh of that joint, so it animates with the body as the runtime attachment does.
Usage: viewer_variants.py <glb> <tag> [<attachment.glb>:<joint> ...] -> review/viewer/mm8_<variant>_<tag>.glb"""
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


def bake(base_doc, base_bin, vi, variant):
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
        mask = np.stack([np.asarray(ch.resize(base.shape[1::-1], Image.Resampling.BILINEAR), np.float32)  # per channel:
                         for ch in image(doc, binary, extras['openyamm_region_mask']['index']).convert('RGBA').split()],
                        -1) / 255                                       # an RGBA resize premultiplies by alpha
        lum = base @ W; out = base.copy()
        for c, reg in enumerate(extras['openyamm_region_ramps']):
            lo, hi = reg['range']; out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
        buf = io.BytesIO(); Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + .5).astype(np.uint8)).save(buf, 'PNG')
        binary.extend(b'\0' * (-len(binary) % 4))
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())}); binary.extend(buf.getvalue())
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'{variant}_baked'})
        doc['textures'].append({'source': len(doc['images']) - 1, **({'sampler': doc['textures'][tex]['sampler']} if 'sampler' in doc['textures'][tex] else {})})
        mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    return doc, binary


def attach(doc, binary, adoc, abin, joint):
    """Append the attachment's level-zero mesh (its node of the joint's name) under the body's joint node."""
    node = next(n for n in adoc['nodes'] if n.get('name') == joint); mesh = copy.deepcopy(adoc['meshes'][node['mesh']])
    mesh.pop('extras', None); off = {k: len(doc.get(k, [])) for k in ('accessors', 'bufferViews', 'images', 'textures', 'materials', 'samplers')}
    binary.extend(b'\0' * (-len(binary) % 16)); boff = len(binary); binary.extend(abin)
    for v in adoc['bufferViews']:
        v = dict(v); v['byteOffset'] = v.get('byteOffset', 0) + boff; doc['bufferViews'].append(v)
    for a in adoc['accessors']:
        a = dict(a); a['bufferView'] += off['bufferViews']; doc['accessors'].append(a)
    for im in adoc.get('images', []):
        im = dict(im); im['bufferView'] += off['bufferViews']; doc['images'].append(im)
    doc.setdefault('samplers', []).extend(adoc.get('samplers', []))
    for t in adoc.get('textures', []):
        t = dict(t); t['source'] += off['images']
        if 'sampler' in t:
            t['sampler'] += off['samplers']
        doc['textures'].append(t)
    def shift(o):
        if isinstance(o, dict):
            return {k: (v + off['textures'] if k == 'index' else shift(v)) for k, v in o.items()}
        return o
    for m in adoc['materials']:
        doc['materials'].append(shift(m))
    for p in mesh['primitives']:
        p['attributes'] = {k: v + off['accessors'] for k, v in p['attributes'].items()}
        p['indices'] += off['accessors']; p['material'] += off['materials']
    doc['meshes'].append(mesh)
    doc['nodes'].append({'name': joint + 'Mesh', 'mesh': len(doc['meshes']) - 1})
    parent = next(n for n in doc['nodes'] if n.get('name') == joint); parent.setdefault('children', []).append(len(doc['nodes']) - 1)


src, tag = Path(sys.argv[1]), sys.argv[2]
base_doc, base_bin = read_glb(src)
atts = []  # MM8 Wasp: any number of attachments (sword and shield)
for arg in sys.argv[3:]:
    apath, joint = arg.rsplit(':', 1); atts.append((read_glb(Path(apath)), joint))
for vi, variant in enumerate(v['name'] for v in base_doc['extensions']['KHR_materials_variants']['variants']):
    doc, binary = bake(base_doc, base_bin, vi, variant)
    for (adoc, abin), joint in atts:
        anames = [v['name'] for v in adoc['extensions']['KHR_materials_variants']['variants']]
        a_doc, a_bin = bake(adoc, abin, anames.index(variant), variant)
        attach(doc, binary, a_doc, bytes(a_bin), joint)
    write_glb(HERE / 'review/viewer' / f'mm8_{variant}_{tag}.glb', doc, bytes(binary))
    print('VIEWER', variant, tag, 'with', [j for _, j in atts])
