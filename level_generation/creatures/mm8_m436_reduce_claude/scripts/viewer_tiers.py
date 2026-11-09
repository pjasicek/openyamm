#!/usr/bin/env python3
"""Browser review GLBs of <glb>, one per palette variant: three.js has no region ramps, so each tier is baked into the
base colour with the engine rule (per region channel c: t = linear luminance normalised over the region's range,
colour = mix(colour, ramp(t), mask[c])). Everything comes from the GLB's own runtime material: the embedded base
colour, the region mask texture named by `openyamm_region_mask` and the ramps of each variant material (M436_A/B/C).
The first version baked the m436 project's 1K body-only textures onto the merged 2080x1024 body+head atlas UVs,
which drew a patchwork over installed and reduced alike. Only the LOD0 node renders in three.js.
Usage: viewer_tiers.py <glb> <tag> -> review/viewer/mm8_<variant>_<tag>.glb"""
import io, json, struct, sys
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
    view = doc['bufferViews'][doc['images'][doc['textures'][texture]['source']]['bufferView']]
    start = view.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(binary[start:start + view['byteLength']])))


def ramp(colors, t):
    c = np.array(colors, np.float32); x = np.clip(t, 0, 1) * (len(c) - 1)
    i = np.minimum(x.astype(int), len(c) - 2); f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


doc0, bin0 = read_glb(GLB)
base_mat = doc0['materials'][doc0['meshes'][0]['primitives'][0]['material']]
base_img = image(doc0, bin0, base_mat['pbrMetallicRoughness']['baseColorTexture']['index']).convert('RGBA')
base = lin(np.asarray(base_img, np.float32)[..., :3] / 255)
mask_img = image(doc0, bin0, base_mat['extras']['openyamm_region_mask']['index']).convert('RGBA')
assert mask_img.size == base_img.size, (mask_img.size, base_img.size)
# per channel: resizing an RGBA image premultiplies by alpha, and unused channels are 0
mask = np.stack([np.asarray(ch, np.float32) / 255 for ch in mask_img.split()], -1)
lum = base @ W
variants = [v['name'] for v in doc0['extensions']['KHR_materials_variants']['variants']]
for vi, variant in enumerate(variants):
    doc, binary = read_glb(GLB)
    prim = doc['meshes'][0]['primitives'][0]
    mat_index = next(m['material'] for m in prim['extensions']['KHR_materials_variants']['mappings'] if vi in m['variants'])
    ramps = doc['materials'][mat_index]['extras']['openyamm_region_ramps']
    out = base.copy()
    for c, reg in enumerate(ramps):
        lo, hi = reg['range']
        out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
    im = Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + 0.5).astype(np.uint8))
    buf = io.BytesIO(); im.save(buf, 'PNG')
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
    binary += buf.getvalue()
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'base_{variant}'})
    mat = doc['materials'][prim['material']]
    info = mat['pbrMetallicRoughness']['baseColorTexture']
    doc['textures'].append(dict(doc['textures'][info['index']], source=len(doc['images']) - 1))
    info['index'] = len(doc['textures']) - 1
    write_glb(HERE / 'review' / 'viewer' / f'mm8_{variant}_{TAG}.glb', doc, binary)
    print('VIEWER', f'mm8_{variant}_{TAG}.glb', 'ramp material', doc['materials'][mat_index]['name'])
