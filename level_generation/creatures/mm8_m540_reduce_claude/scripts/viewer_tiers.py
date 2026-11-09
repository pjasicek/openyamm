#!/usr/bin/env python3
"""Browser review GLBs of <glb> per palette tier: three.js has no region ramps, so each variant material's ramp
(material extras openyamm_region_ramps over the openyamm_region_mask channels, engine rule: t = linear luminance
normalised over the region's range, colour = mix(colour, ramp(t), mask)) is baked into the merged body/head atlas,
every primitive uses that tier's material, and the installed wand (static, attached to the Wand bone) is added as a
child node of the Wand joint. Usage: viewer_tiers.py <glb> <tag> -> review/viewer/mm8_m540_<a|b|c>_<tag>.glb"""
import io, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
GLB, TAG = Path(sys.argv[1]), sys.argv[2]
WAND = HERE / 'work/mm8_m540_wand_source_pre_reduce.glb'
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


def image(doc, binary, index):
    v = doc['bufferViews'][doc['images'][doc['textures'][index]['source']]['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(binary[o:o + v['byteLength']])))


def ramp(colors, t):
    c = np.array(colors, np.float32); x = np.clip(t, 0, 1) * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2); f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


def add_image(doc, binary, im, name, like):
    buf = io.BytesIO(); im.save(buf, 'PNG'); binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
    binary += buf.getvalue()
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': name})
    doc['textures'].append(dict(doc['textures'][like], source=len(doc['images']) - 1))
    return len(doc['textures']) - 1


def attach_wand(doc, binary, mat_index):
    """Append the wand's LOD0 mesh, its material for this tier and textures; node child of the Wand joint."""
    wd, wb = read_glb(WAND)
    binary += b'\0' * (-len(binary) % 4); base = len(binary); binary += wb
    vo, ao, io_, to = len(doc['bufferViews']), len(doc['accessors']), len(doc['images']), len(doc['textures'])
    doc['bufferViews'] += [dict(v, buffer=0, byteOffset=v.get('byteOffset', 0) + base) for v in wd['bufferViews']]
    doc['accessors'] += [dict(a, bufferView=a['bufferView'] + vo) for a in wd['accessors']]
    doc['images'] += [dict(i, bufferView=i['bufferView'] + vo) for i in wd['images']]
    so = len(doc.setdefault('samplers', []))
    doc['samplers'] += wd.get('samplers', [])
    doc['textures'] += [dict(t, source=t['source'] + io_, **({'sampler': t['sampler'] + so} if 'sampler' in t else {}))
                        for t in wd['textures']]
    def shift(o):
        if isinstance(o, dict):
            return {k: (v + to if k == 'index' and isinstance(v, int) else shift(v)) for k, v in o.items()}
        return [shift(x) for x in o] if isinstance(o, list) else o
    mat = shift(wd['materials'][mat_index]); mat.pop('extras', None); doc['materials'].append(mat)
    m = wd['meshes'][wd['nodes'][0]['mesh']]
    prims = [{'attributes': {k: v + ao for k, v in p['attributes'].items()}, 'indices': p['indices'] + ao,
              'material': len(doc['materials']) - 1} for p in m['primitives']]
    doc['meshes'].append({'name': 'Wand', 'primitives': prims})
    wn = {k: v for k, v in wd['nodes'][0].items() if k != 'mesh'}; wn.update(name='WandMesh', mesh=len(doc['meshes']) - 1)
    doc['nodes'].append(wn)
    joint = next(n for n in doc['nodes'] if n.get('name') == 'Wand' and 'mesh' not in n)
    joint.setdefault('children', []).append(len(doc['nodes']) - 1)


for tier, variant in enumerate('abc'):
    doc, binary = read_glb(GLB)
    mat = doc['materials'][tier]; ex = mat['extras']
    base = image(doc, binary, mat['pbrMetallicRoughness']['baseColorTexture']['index']).convert('RGBA')
    rgba = np.asarray(base, np.float32) / 255; lb = lin(rgba[..., :3])
    mask = np.asarray(image(doc, binary, ex['openyamm_region_mask']['index']).convert('RGBA').resize(base.size, Image.BILINEAR), np.float32) / 255
    lum = lb @ W; out = lb.copy()
    for c, reg in enumerate(ex['openyamm_region_ramps']):
        lo, hi = reg['range']
        out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
    im = Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + .5).astype(np.uint8))
    info = mat['pbrMetallicRoughness']['baseColorTexture']
    info['index'] = add_image(doc, binary, im, f'm540_{variant}_baked', info['index'])
    for m in doc['meshes']:
        for p in m['primitives']:
            p['material'] = tier; p.pop('extensions', None)
    attach_wand(doc, binary, tier)
    doc.pop('extensions', None); doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants']
    if not doc['extensionsUsed']:
        doc.pop('extensionsUsed')
    out_path = HERE / 'review' / 'viewer' / f'mm8_m540_{variant}_{TAG}.glb'; out_path.parent.mkdir(parents=True, exist_ok=True)
    write_glb(out_path, doc, binary)
    print('VIEWER', out_path.name)
