#!/usr/bin/env python3
"""Review-viewer GLBs for the reduction (three.js has no region ramps): each KHR_materials_variants tier material of
<glb> (M238_A/B/C, one region: the green cloth) is baked into its base colour with the engine rule (t = linear
luminance normalised over the region's range, colour = mix(colour, ramp(t), mask channel); ramps from the material
extras) and assigned to the body's full-detail primitive. Everything else stays (the lamp mesh, the collapsed-mesh
node keys that hide the body in Dead and the lamp while alive, the clips); LOD and shadow meshes are only referenced
from extras, which three.js ignores. Writes review/viewer/mm7_m238_<label>_<a|b|c>.glb inside this project only.
Usage: viewer_tiers.py <glb> <label>"""
import copy, io, sys
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


def img(i):
    bv = D['bufferViews'][D['images'][i]['bufferView']]; o = bv.get('byteOffset', 0)
    return Image.open(io.BytesIO(B[o:o + bv['byteLength']]))


body_node = next(n for n in D['nodes'] if n.get('name') == 'M238')
for mat in [m for m in D['materials'] if m['name'].startswith('M238_')]:
    tier = mat['name'].split('_')[-1].lower()
    doc = copy.deepcopy(D); binary = bytearray(B)
    base_img = img(D['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source']).convert('RGBA')
    rgba = np.asarray(base_img, np.float32) / 255
    mask = np.stack([np.asarray(ch.resize(base_img.size, Image.BILINEAR), np.float32) / 255
                     for ch in img(D['textures'][mat['extras']['openyamm_region_mask']['index']]['source']).convert('RGBA').split()], -1)
    base = lin(rgba[..., :3]); lum = base @ W; out = base.copy()
    for c, reg in enumerate(mat['extras']['openyamm_region_ramps']):
        lo, hi = reg['range']
        out = out * (1 - mask[..., c:c + 1]) + ramp(reg['colors'], (lum - lo) / (hi - lo)) * mask[..., c:c + 1]
    buf = io.BytesIO(); Image.fromarray((np.clip(srgb(out), 0, 1) * 255 + .5).astype(np.uint8)).save(buf, 'PNG')
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
    binary.extend(buf.getvalue())
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'baked_{tier}'})
    t0 = doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]
    doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': t0.get('sampler', 0)})
    m = copy.deepcopy(mat); m.pop('extras', None); m['name'] = f'M238_{tier.upper()}_baked'
    m['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    doc['materials'].append(m)
    for p in doc['meshes'][body_node['mesh']]['primitives']:
        p.pop('extensions', None); p['material'] = len(doc['materials']) - 1
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            p.pop('extensions', None)
    doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants']
    if not doc['extensionsUsed']:
        doc.pop('extensionsUsed')
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    if 'extensions' in doc and not doc['extensions']:
        doc.pop('extensions')
    doc['buffers'][0]['byteLength'] = len(binary)
    out_path = ROOT / 'review' / 'viewer' / f'mm7_m238_{label}_{tier}.glb'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_glb(out_path, doc, bytes(binary)); print('VIEWER', out_path.name, f'{out_path.stat().st_size / 1e6:.1f} MB')
